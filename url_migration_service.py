#!/usr/bin/env python3
"""
MongoDB URL Migration Service
Continuously polls MongoDB collections and replaces old IP addresses with new domain
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, List
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('url_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class URLMigrationService:
    """Service to migrate URLs from old IP to new domain"""
    
    def __init__(self):
        # MongoDB configuration
        self.mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        self.db_name = os.getenv('MONGO_DB_NAME', 'wearapp')
        
        # URL replacement configuration
        self.old_url = os.getenv('OLD_URL', 'http://155.248.254.206:9000')
        self.new_url = os.getenv('NEW_URL', 'https://images.nomo.software')
        
        # Polling interval
        self.poll_interval = int(os.getenv('POLL_INTERVAL', '1'))
        
        # Collection configurations
        self.groundtruth_collection = os.getenv('GROUNDTRUTH_COLLECTION', 'imageUrl')
        self.user_clothes_collection = os.getenv('USER_CLOTHES_COLLECTION', 'userUploadedClothes')
        
        # Initialize MongoDB client
        self.client = None
        self.db = None
        
        # Statistics
        self.stats = {
            'groundtruth_updated': 0,
            'user_clothes_updated': 0,
            'errors': 0,
            'last_check': None
        }
    
    def connect_db(self):
        """Establish MongoDB connection"""
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            # Test connection
            self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {self.mongo_uri}")
            logger.info(f"Database: {self.db_name}")
            logger.info(f"Old URL: {self.old_url}")
            logger.info(f"New URL: {self.new_url}")
            return True
        except PyMongoError as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def replace_url_in_dict(self, data: Dict, fields: List[str]) -> tuple:
        """
        Replace old URL with new URL in specified fields
        Returns (modified_data, was_modified)
        """
        modified = False
        
        for field in fields:
            if field in data and data[field] and isinstance(data[field], str):
                if self.old_url in data[field]:
                    data[field] = data[field].replace(self.old_url, self.new_url)
                    modified = True
                    logger.debug(f"Replaced URL in field '{field}'")
        
        return data, modified
    
    def process_groundtruth_collection(self):
        """Process documents in groundtruth imageUrl collection"""
        try:
            collection = self.db[self.groundtruth_collection]
            
            # Fields to check for URL replacement
            url_fields = [
                'minioUrl',
                's3Url',
                'minioUrlOracle',
                'minioUrlThinker'
            ]
            
            # Find documents containing the old URL
            query = {
                '$or': [
                    {field: {'$regex': self.old_url.replace('/', '\\/'), '$options': 'i'}}
                    for field in url_fields
                ]
            }
            
            documents = collection.find(query)
            updated_count = 0
            
            for doc in documents:
                doc_id = doc['_id']
                modified_doc, was_modified = self.replace_url_in_dict(doc, url_fields)
                
                if was_modified:
                    # Remove _id for update
                    modified_doc.pop('_id', None)
                    
                    # Update document
                    result = collection.update_one(
                        {'_id': doc_id},
                        {'$set': modified_doc}
                    )
                    
                    if result.modified_count > 0:
                        updated_count += 1
                        logger.info(f"Updated groundtruth document: {doc_id}")
            
            if updated_count > 0:
                self.stats['groundtruth_updated'] += updated_count
                logger.info(f"Groundtruth: Updated {updated_count} documents")
            
            return updated_count
            
        except PyMongoError as e:
            logger.error(f"Error processing groundtruth collection: {e}")
            self.stats['errors'] += 1
            return 0
    
    def process_user_clothes_collection(self):
        """Process documents in userUploadedClothes collection"""
        try:
            collection = self.db[self.user_clothes_collection]
            
            # Fields to check for URL replacement
            url_fields = [
                'imageUrl',
                'segmentedImageUrl'
            ]
            
            # Find documents containing the old URL
            query = {
                '$or': [
                    {field: {'$regex': self.old_url.replace('/', '\\/'), '$options': 'i'}}
                    for field in url_fields
                ]
            }
            
            documents = collection.find(query)
            updated_count = 0
            
            for doc in documents:
                doc_id = doc['_id']
                modified_doc, was_modified = self.replace_url_in_dict(doc, url_fields)
                
                if was_modified:
                    # Remove _id for update
                    modified_doc.pop('_id', None)
                    
                    # Add updatedAt timestamp
                    modified_doc['updatedAt'] = datetime.utcnow()
                    
                    # Update document
                    result = collection.update_one(
                        {'_id': doc_id},
                        {'$set': modified_doc}
                    )
                    
                    if result.modified_count > 0:
                        updated_count += 1
                        logger.info(f"Updated user clothes document: {doc_id}")
            
            if updated_count > 0:
                self.stats['user_clothes_updated'] += updated_count
                logger.info(f"User Clothes: Updated {updated_count} documents")
            
            return updated_count
            
        except PyMongoError as e:
            logger.error(f"Error processing user clothes collection: {e}")
            self.stats['errors'] += 1
            return 0
    
    def run_check(self):
        """Run a single check cycle"""
        logger.debug("Running check cycle...")
        
        groundtruth_count = self.process_groundtruth_collection()
        user_clothes_count = self.process_user_clothes_collection()
        
        self.stats['last_check'] = datetime.utcnow()
        
        if groundtruth_count > 0 or user_clothes_count > 0:
            logger.info(f"Check complete - GT: {groundtruth_count}, UC: {user_clothes_count}")
    
    def print_stats(self):
        """Print service statistics"""
        logger.info("=" * 60)
        logger.info("Service Statistics:")
        logger.info(f"  Groundtruth documents updated: {self.stats['groundtruth_updated']}")
        logger.info(f"  User clothes documents updated: {self.stats['user_clothes_updated']}")
        logger.info(f"  Total errors: {self.stats['errors']}")
        logger.info(f"  Last check: {self.stats['last_check']}")
        logger.info("=" * 60)
    
    def run(self):
        """Main service loop"""
        logger.info("Starting URL Migration Service...")
        
        if not self.connect_db():
            logger.error("Failed to connect to database. Exiting.")
            return
        
        logger.info(f"Polling interval: {self.poll_interval} second(s)")
        logger.info("Service running. Press Ctrl+C to stop.")
        
        try:
            while True:
                try:
                    self.run_check()
                    time.sleep(self.poll_interval)
                    
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logger.error(f"Error in check cycle: {e}")
                    self.stats['errors'] += 1
                    time.sleep(self.poll_interval)
                    
        except KeyboardInterrupt:
            logger.info("\nShutting down service...")
            self.print_stats()
            
        finally:
            if self.client:
                self.client.close()
                logger.info("MongoDB connection closed")


def main():
    """Main entry point"""
    service = URLMigrationService()
    service.run()


if __name__ == "__main__":
    main()
