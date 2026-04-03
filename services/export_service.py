import csv
from .log_service import LogService


class ExportService:
    @staticmethod
    def export_to_csv(users, file_path):
        """导出用户到 CSV（dsadd 兼容格式）"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # dsadd 格式：序号,显示名,姓,名,用户名,密码
                writer.writerow(['序号', '显示名称', '姓氏', '名字', '用户名', '密码'])
                for i, u in enumerate(users, 1):
                    writer.writerow([
                        i,
                        u.get('display_name', ''),
                        u.get('last_name', ''),
                        u.get('first_name', ''),
                        u.get('username', ''),
                        ''  # 密码留空
                    ])
            LogService.log(f'Exported {len(users)} users to {file_path}')
        except Exception as ex:
            LogService.log_error('Export CSV failed', ex)
            raise Exception(f'导出CSV失败: {ex}')

    @staticmethod
    def import_from_csv(file_path):
        """导入 CSV，自动识别编码和格式"""
        users = []

        # 尝试多种编码
        encodings = ['utf-8-sig', 'gbk', 'gb2312', 'utf-8']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                # 解码成功，处理内容
                lines = content.strip().split('\n')
                if len(lines) < 2:
                    continue

                for line in lines[1:]:  # skip header
                    if not line.strip():
                        continue
                    row = [cell.strip() for cell in line.split(',')]

                    if len(row) == 6:
                        # dsadd 格式：序号,显示名,姓,名,用户名,密码
                        if row[4]:
                            users.append({
                                'username': row[4],
                                'display_name': row[1],
                                'first_name': row[3],
                                'last_name': row[2],
                                'password': row[5] if row[5] else 'Pass@123',
                                'email': '',
                                'department': '',
                                'title': '',
                                'enabled': True
                            })
                    elif len(row) >= 5:
                        # 标准格式
                        if row[0]:
                            users.append({
                                'username': row[0],
                                'display_name': row[1],
                                'first_name': row[2],
                                'last_name': row[3],
                                'email': row[4] if len(row) > 4 else '',
                                'department': row[5] if len(row) > 5 else '',
                                'title': row[6] if len(row) > 6 else '',
                                'enabled': row[7].lower() == 'true' if len(row) > 7 else True,
                                'password': row[8] if len(row) > 8 and row[8] else 'Pass@123'
                            })

                LogService.log(f'Imported {len(users)} users from {file_path} (encoding: {encoding})')
                return users

            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as ex:
                LogService.log_error(f'Import CSV failed with {encoding}', ex)
                continue

        raise Exception('无法识别文件编码，请将CSV文件另存为 UTF-8 或 GBK 编码')