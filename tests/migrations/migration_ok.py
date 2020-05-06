"""Testing migration
"""

dependencies = ['abcd']


def upgrade(db):    
    print('upgrade!')


def downgrade(db):
    print('downgrade!')
