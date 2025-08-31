#!/usr/bin/env python3
"""
Demo data generator for Chat with Your Data.
Creates sample data to demonstrate the RAG system without requiring a real database.
"""

import json
from datetime import datetime, timedelta
import random

def generate_sample_articles():
    """Generate sample articles for demonstration."""
    
    sample_articles = [
        {
            "id": 1,
            "title": "Introduction to Machine Learning",
            "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It involves algorithms that can identify patterns in data and make predictions or decisions based on those patterns.",
            "category": "Technology",
            "author": "Dr. Sarah Johnson",
            "created_at": "2024-01-15T10:30:00",
            "tags": ["machine learning", "AI", "data science"]
        },
        {
            "id": 2,
            "title": "Benefits of Cloud Computing",
            "content": "Cloud computing offers numerous advantages including cost efficiency, scalability, flexibility, and disaster recovery. Organizations can reduce IT infrastructure costs while gaining access to enterprise-level technology and services on demand.",
            "category": "Technology",
            "author": "Mike Chen",
            "created_at": "2024-01-20T14:15:00",
            "tags": ["cloud computing", "infrastructure", "cost savings"]
        },
        {
            "id": 3,
            "title": "Sustainable Energy Solutions",
            "content": "Renewable energy sources like solar, wind, and hydroelectric power are becoming increasingly important for sustainable development. These clean energy solutions help reduce carbon emissions and provide long-term environmental benefits.",
            "category": "Environment",
            "author": "Dr. Emma Green",
            "created_at": "2024-01-25T09:45:00",
            "tags": ["renewable energy", "sustainability", "environment"]
        },
        {
            "id": 4,
            "title": "Remote Work Best Practices",
            "content": "Effective remote work requires clear communication, proper time management, dedicated workspace setup, and regular team collaboration. Tools like video conferencing, project management software, and cloud storage are essential for success.",
            "category": "Business",
            "author": "Lisa Wang",
            "created_at": "2024-02-01T11:20:00",
            "tags": ["remote work", "productivity", "collaboration"]
        },
        {
            "id": 5,
            "title": "Data Privacy in Digital Age",
            "content": "Data privacy has become a critical concern as digital transformation accelerates. Organizations must implement robust security measures, comply with regulations like GDPR, and maintain transparency about data collection and usage practices.",
            "category": "Security",
            "author": "Robert Kim",
            "created_at": "2024-02-05T16:00:00",
            "tags": ["data privacy", "security", "GDPR", "compliance"]
        },
        {
            "id": 6,
            "title": "The Future of Electric Vehicles",
            "content": "Electric vehicles are revolutionizing transportation with improved battery technology, expanded charging infrastructure, and government incentives. The EV market is expected to grow significantly over the next decade.",
            "category": "Technology",
            "author": "Tom Anderson",
            "created_at": "2024-02-10T13:30:00",
            "tags": ["electric vehicles", "transportation", "sustainability"]
        },
        {
            "id": 7,
            "title": "Artificial Intelligence in Healthcare",
            "content": "AI applications in healthcare include medical imaging analysis, drug discovery, personalized treatment plans, and predictive analytics. These technologies are improving patient outcomes and reducing healthcare costs.",
            "category": "Healthcare",
            "author": "Dr. Maria Rodriguez",
            "created_at": "2024-02-15T10:15:00",
            "tags": ["AI", "healthcare", "medical technology", "patient care"]
        },
        {
            "id": 8,
            "title": "Blockchain Technology Explained",
            "content": "Blockchain is a distributed ledger technology that provides transparency, security, and decentralization. Beyond cryptocurrencies, blockchain has applications in supply chain management, voting systems, and digital identity verification.",
            "category": "Technology",
            "author": "David Lee",
            "created_at": "2024-02-20T15:45:00",
            "tags": ["blockchain", "cryptocurrency", "distributed systems"]
        },
        {
            "id": 9,
            "title": "Mental Health in the Workplace",
            "content": "Workplace mental health initiatives are crucial for employee wellbeing and productivity. Companies are implementing stress management programs, flexible work arrangements, and mental health support resources.",
            "category": "Health",
            "author": "Dr. Jennifer Smith",
            "created_at": "2024-02-25T12:00:00",
            "tags": ["mental health", "workplace wellness", "employee support"]
        },
        {
            "id": 10,
            "title": "Cybersecurity Trends 2024",
            "content": "Emerging cybersecurity threats include AI-powered attacks, IoT vulnerabilities, and social engineering. Organizations must adopt zero-trust security models, implement multi-factor authentication, and conduct regular security training.",
            "category": "Security",
            "author": "Alex Thompson",
            "created_at": "2024-03-01T14:30:00",
            "tags": ["cybersecurity", "threats", "zero-trust", "security training"]
        }
    ]
    
    return sample_articles

def save_sample_data():
    """Save sample data to JSON files."""
    articles = generate_sample_articles()
    
    # Save to JSON file
    with open('sample_articles.json', 'w', encoding='utf-8') as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Generated {len(articles)} sample articles")
    print("📄 Saved to sample_articles.json")
    
    return articles

def create_demo_database_config():
    """Create demo configuration examples."""
    
    # PostgreSQL example config
    postgres_config = {
        "db_type": "postgresql",
        "connection_params": {
            "host": "localhost",
            "port": 5432,
            "user": "demo_user",
            "password": "demo_password",
            "database": "demo_db"
        },
        "table_or_collection": "articles",
        "columns_or_fields": ["id", "title", "content", "category", "author", "created_at"],
        "text_fields": ["title", "content", "category", "author"]
    }
    
    # MongoDB example config
    mongodb_config = {
        "db_type": "mongodb",
        "connection_params": {
            "host": "localhost",
            "port": 27017,
            "user": "demo_user",
            "password": "demo_password",
            "database": "demo_db"
        },
        "table_or_collection": "articles",
        "columns_or_fields": ["_id", "title", "content", "category", "author", "created_at"],
        "text_fields": ["title", "content", "category", "author"]
    }
    
    # Save config examples
    with open('demo_postgres_config.json', 'w') as f:
        json.dump(postgres_config, f, indent=2)
    
    with open('demo_mongodb_config.json', 'w') as f:
        json.dump(mongodb_config, f, indent=2)
    
    print("✅ Created demo database configuration files:")
    print("   - demo_postgres_config.json")
    print("   - demo_mongodb_config.json")

def main():
    """Main function to generate demo data."""
    print("🎯 Generating Demo Data for Chat with Your Data")
    print("=" * 50)
    
    # Generate sample articles
    articles = save_sample_data()
    
    # Create demo configs
    create_demo_database_config()
    
    print("\n📋 Demo Data Generated Successfully!")
    print("\nNext Steps:")
    print("1. Set up your database (PostgreSQL or MongoDB)")
    print("2. Import the sample data into your database")
    print("3. Update your .env file with database credentials")
    print("4. Use the demo config files as templates for the /ingest-data endpoint")
    print("5. Start the server and begin chatting with your data!")
    
    print("\n💡 Sample Questions to Try:")
    print("   - What articles do you have about technology?")
    print("   - Tell me about machine learning")
    print("   - Show me recent articles from February 2024")
    print("   - What topics does Dr. Sarah Johnson write about?")
    print("   - Find articles related to security and privacy")

if __name__ == "__main__":
    main()
