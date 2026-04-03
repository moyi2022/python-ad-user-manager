class UserDto:
    def __init__(self, data=None):
        data = data or {}
        self.username = data.get('username', '')
        self.display_name = data.get('display_name', '')
        self.first_name = data.get('first_name', '')
        self.last_name = data.get('last_name', '')
        self.email = data.get('email', '')
        self.department = data.get('department', '')
        self.title = data.get('title', '')
        self.password = data.get('password', '')
        self.enabled = data.get('enabled', True)

    def to_dict(self):
        return {
            'username': self.username,
            'display_name': self.display_name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'department': self.department,
            'title': self.title,
            'enabled': self.enabled
        }
