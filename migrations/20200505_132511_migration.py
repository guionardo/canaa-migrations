"""Creating 1000 numbers"""

# Include here the dependent previous migrations names (files)
dependencies = ['20200505_125612_migration']

# Upgrade actions
# db is an pymongo
def upgrade(db) -> bool:
    db.numbers_collection.insert_many([{"i": i} for i in range(1000)])
    return True

# Downgrade actions
def downgrade(db) -> bool:
    db.numbers_collection.drop()
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
