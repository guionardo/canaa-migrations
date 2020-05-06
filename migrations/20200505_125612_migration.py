"""Creating texts"""
import random

# Include here the dependent previous migrations names (files)
dependencies = []

# Upgrade actions
# db is an pymongo


def upgrade(db) -> bool:
    db.names_collection.insert_many([{"name": rand_text(10)} for _ in range(100)])    
    return True

# Downgrade actions


def downgrade(db) -> bool:
    db.names_collection.drop()
    return True

# after_upgrade (optional) is called after the upgrade methods
# raised_exception is None if the upgrade was successful
# Must return a boolean True if the migration process can continue


def after_upgrade(raised_exception: Exception) -> bool:
    return True

# after_downgrade (optional) is called after the downgrade methods
# raised_exception is None if the downgrade was successful
# Must return a boolean True if the migration process can continue


def after_downgrade(raised_exception: Exception) -> bool:
    return True


def rand_text(length=10):
    return ''.join([chr(random.randint(65, 93)) for _ in range(length)])
