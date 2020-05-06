"""Testing migration
"""

dependencies = ['abcd']


def upgrade(db, excessive_arg):
    print('upgrade!')


def downgrade_(db):
    """
    Where is downgrade?
    """
    print('downgrade!')
