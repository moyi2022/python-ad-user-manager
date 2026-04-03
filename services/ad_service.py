from ldap3 import Server, Connection, ALL, SUBTREE, MODIFY_REPLACE, MODIFY_DELETE, MODIFY_ADD
from .log_service import LogService


class AdService:
    def __init__(self):
        self._server = None
        self._conn = None
        self._server_host = '10.182.0.121'  # LDAP 服务器地址
        self._domain_suffix = 'jtw.local'     # UPN 后缀
        self._base_dn = 'DC=jtw,DC=local'
        self._user_dn_template = 'CN={},CN=Users,DC=jtw,DC=local'

    def connect(self, username, password):
        try:
            self._server = Server(f'ldap://{self._server_host}', get_info=ALL)
            # 使用 UPN 格式登录
            user_upn = f'{username}@{self._domain_suffix}'
            self._conn = Connection(self._server, user=user_upn, password=password, auto_bind=True)
            LogService.log(f'Connected to {self._server_host} as {username}')
            return True
        except Exception as ex:
            LogService.log_error('Failed to connect to AD', ex)
            raise Exception(f'无法连接到域控制器: {ex}')

    def disconnect(self):
        if self._conn:
            self._conn.unbind()
            self._conn = None
            LogService.log('Disconnected from domain')

    def get_all_users(self, base_dn=None):
        try:
            users = []
            search_base = base_dn if base_dn else self._base_dn
            self._conn.search(
                search_base=search_base,
                search_filter='(&(objectClass=user)(!(objectClass=computer)))',
                search_scope=SUBTREE,
                attributes=[
                    'sAMAccountName', 'displayName', 'givenName', 'sn',
                    'mail', 'department', 'title', 'userAccountControl',
                    'distinguishedName'
                ]
            )
            for entry in self._conn.entries:
                uac = int(entry.userAccountControl.value) if hasattr(entry, 'userAccountControl') and entry.userAccountControl else 0
                disabled = (uac & 2) != 0
                dn = str(entry.distinguishedName) if hasattr(entry, 'distinguishedName') and entry.distinguishedName else ''
                users.append({
                    'username': str(entry.sAMAccountName) if hasattr(entry, 'sAMAccountName') and entry.sAMAccountName else '',
                    'display_name': str(entry.displayName) if hasattr(entry, 'displayName') and entry.displayName else '',
                    'first_name': str(entry.givenName) if hasattr(entry, 'givenName') and entry.givenName else '',
                    'last_name': str(entry.sn) if hasattr(entry, 'sn') and entry.sn else '',
                    'email': str(entry.mail) if hasattr(entry, 'mail') and entry.mail else '',
                    'department': str(entry.department) if hasattr(entry, 'department') and entry.department else '',
                    'title': str(entry.title) if hasattr(entry, 'title') and entry.title else '',
                    'enabled': not disabled,
                    'dn': dn
                })
            LogService.log(f'Retrieved {len(users)} users from {search_base}')
            return users
        except Exception as ex:
            LogService.log_error('Failed to get users', ex)
            raise Exception(f'获取用户列表失败: {ex}')

    def create_user(self, user, ou_dn=None):
        try:
            if ou_dn:
                user_dn = f'CN={user.get("username")},{ou_dn}'
            else:
                user_dn = f'CN={user.get("username")},CN=Users,{self._base_dn}'

            # AD 创建用户流程：先创建禁用账户，设置密码后再启用
            attrs = {
                'objectClass': ['top', 'person', 'organizationalPerson', 'user'],
                'sAMAccountName': user.get('username'),
                'userAccountControl': 544  # NORMAL_ACCOUNT + PASSWD_NOTREQD (允许无密码创建)
            }

            # 只添加有值的属性，避免空字符串导致 AD 错误
            display_name = user.get('display_name', '').strip()
            if display_name:
                attrs['displayName'] = display_name
            else:
                attrs['displayName'] = user.get('username')  # 必须有 displayName

            first_name = user.get('first_name', '').strip()
            if first_name:
                attrs['givenName'] = first_name

            last_name = user.get('last_name', '').strip()
            if last_name:
                attrs['sn'] = last_name

            email = user.get('email', '').strip()
            if email:
                attrs['mail'] = email

            department = user.get('department', '').strip()
            if department:
                attrs['department'] = department

            title = user.get('title', '').strip()
            if title:
                attrs['title'] = title

            result = self._conn.add(user_dn, attributes=attrs)
            if not result:
                # 检查操作结果
                if hasattr(self._conn, 'result') and self._conn.result:
                    error_msg = self._conn.result.get('description', str(self._conn.result))
                else:
                    error_msg = '未知错误'
                raise Exception(f'LDAP add 失败: {error_msg}')

            # 设置密码
            if user.get('password'):
                self._set_password(user_dn, user.get('password'))

            # 启用账户
            if user.get('enabled', True):
                self._conn.modify(user_dn, {'userAccountControl': [(MODIFY_REPLACE, ['512'])]})

            LogService.log(f'Created user: {user.get("username")}')
            return True
        except Exception as ex:
            LogService.log_error(f'Failed to create user {user.get("username")}', ex)
            raise Exception(f'创建用户失败: {ex}')

    def update_user(self, original_username, user, user_dn=None):
        try:
            if user_dn is None:
                user_dn = self._user_dn_template.format(original_username)
            changes = {}
            # 只替换有值的字段，空值时跳过（AD 有些字段不能为空）
            for field, ldap_attr in [
                ('display_name', 'displayName'),
                ('first_name', 'givenName'),
                ('last_name', 'sn'),
                ('email', 'mail'),
                ('department', 'department'),
                ('title', 'title'),
            ]:
                val = user.get(field, '')
                if val:
                    changes[ldap_attr] = [(MODIFY_REPLACE, [val])]
            # 启用/禁用
            if 'enabled' in user:
                uac = 512 if user['enabled'] else 514
                changes['userAccountControl'] = [(MODIFY_REPLACE, [str(uac)])]
            if changes:
                self._conn.modify(user_dn, changes)
            LogService.log(f'Updated user: {user.get("username")}')
            return True
        except Exception as ex:
            LogService.log_error(f'Failed to update user {original_username}', ex)
            raise Exception(f'更新用户失败: {ex}')

    def delete_user(self, username, user_dn=None):
        try:
            if user_dn is None:
                user_dn = self._user_dn_template.format(username)
            self._conn.delete(user_dn)
            LogService.log(f'Deleted user: {username}')
            return True
        except Exception as ex:
            LogService.log_error(f'Failed to delete user {username}', ex)
            raise Exception(f'删除用户失败: {ex}')

    def reset_password(self, username, new_password, user_dn=None):
        try:
            if user_dn is None:
                user_dn = self._user_dn_template.format(username)
            self._set_password(user_dn, new_password)
            LogService.log(f'Reset password for user: {username}')
            return True
        except Exception as ex:
            LogService.log_error(f'Failed to reset password for {username}', ex)
            raise Exception(f'重置密码失败: {ex}')

    def _set_password(self, user_dn, password):
        # AD 要求密码用 UTF-16LE 编码并加双引号
        password_bytes = ('"' + password + '"').encode('utf-16-le')
        self._conn.modify(user_dn, {'unicodePwd': [(MODIFY_REPLACE, [password_bytes])]})

    def get_ous(self):
        """获取所有 OU 和容器"""
        try:
            ous = []
            self._conn.search(
                search_base=self._base_dn,
                search_filter='(|(objectClass=organizationalUnit)(objectClass=container)(objectClass=builtinDomain))',
                search_scope=SUBTREE,
                attributes=['distinguishedName', 'name', 'description']
            )
            for entry in self._conn.entries:
                dn = str(entry.distinguishedName) if hasattr(entry, 'distinguishedName') and entry.distinguishedName else ''
                name = str(entry.name) if hasattr(entry, 'name') and entry.name else ''
                if 'CN=ForeignSecurityPrincipals' not in dn and 'CN=Program Data' not in dn:
                    ous.append({
                        'dn': dn,
                        'name': name or self._get_cn_from_dn(dn)
                    })
            LogService.log(f'Retrieved {len(ous)} OUs/containers')
            return ous
        except Exception as ex:
            LogService.log_error('Failed to get OUs', ex)
            return []

    def _get_cn_from_dn(self, dn):
        """从 DN 中提取 CN 名称"""
        if dn.startswith('CN='):
            parts = dn.split(',')
            if parts:
                return parts[0].replace('CN=', '')
        return dn
