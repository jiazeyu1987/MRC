from typing import List, Dict, Optional, Any
from flask import current_app
from app import db
from app.models import Role, SessionRole


class RoleService:
    """角色服务类"""

    @staticmethod
    def get_roles_count() -> int:
        """
        获取角色总数

        Returns:
            int: 角色总数
        """
        try:
            return Role.query.count()
        except Exception:
            # 如果查询失败，返回0
            return 0

    @staticmethod
    def get_all_roles() -> List[Role]:
        """
        获取所有角色

        Returns:
            List[Role]: 角色列表
        """
        try:
            return Role.query.all()
        except Exception:
            # 如果查询失败，返回空列表
            return []

    @staticmethod
    def get_active_roles() -> List[Role]:
        """
        获取活跃角色

        Returns:
            List[Role]: 活跃角色列表
        """
        try:
            return Role.query.filter_by(is_active=True).all()
        except Exception:
            # 如果查询失败，返回空列表
            return []

    @staticmethod
    def get_role_by_id(role_id: int) -> Optional[Role]:
        """
        根据ID获取角色

        Args:
            role_id: 角色ID

        Returns:
            Optional[Role]: 角色对象或None
        """
        try:
            return Role.query.get(role_id)
        except Exception:
            return None

    @staticmethod
    def get_builtin_roles() -> List[Role]:
        """
        获取内置角色

        Returns:
            List[Role]: 内置角色列表
        """
        try:
            return Role.query.filter_by(is_builtin=True).all()
        except Exception:
            # 如果查询失败，返回空列表
            return []

    @staticmethod
    def get_roles_by_type(role_type: str) -> List[Role]:
        """
        根据类型获取角色

        Args:
            role_type: 角色类型

        Returns:
            List[Role]: 指定类型的角色列表
        """
        try:
            return Role.query.filter_by(type=role_type).all()
        except Exception:
            # 如果查询失败，返回空列表
            return []

    @staticmethod
    def get_deletion_statistics(search_filter: str = '') -> Dict[str, Any]:
        """
        获取角色删除统计信息

        Args:
            search_filter: 搜索过滤条件

        Returns:
            Dict: 包含统计信息的字典
        """
        try:
            query = Role.query

            # 应用搜索过滤
            if search_filter:
                from sqlalchemy import or_
                query = query.filter(
                    or_(Role.name.contains(search_filter),
                        Role.prompt.contains(search_filter))
                )

            total_roles = query.count()

            # 查找被会话使用的角色
            used_role_ids = db.session.query(SessionRole.role_id).distinct().all()
            used_role_ids = [row[0] for row in used_role_ids]

            if search_filter:
                # 如果有搜索条件，需要重新查询被使用的角色
                used_roles_query = query.filter(Role.id.in_(used_role_ids))
                used_roles = used_roles_query.count()
                deletable_roles = total_roles - used_roles
            else:
                used_roles = len(used_role_ids)
                deletable_roles = total_roles - used_roles

            return {
                'total_roles': total_roles,
                'deletable_roles': deletable_roles,
                'used_roles': used_roles,
                'search_filter': search_filter
            }

        except Exception as e:
            current_app.logger.error(f"获取角色删除统计失败: {str(e)}")
            return {
                'total_roles': 0,
                'deletable_roles': 0,
                'used_roles': 0,
                'search_filter': search_filter
            }

    @staticmethod
    def bulk_delete_roles(search_filter: str = '', confirm: bool = False) -> Dict[str, Any]:
        """
        批量删除角色（仅删除未被会话使用的角色）

        Args:
            search_filter: 搜索过滤条件
            confirm: 确认标记

        Returns:
            Dict: 包含删除结果的字典
        """
        if not confirm:
            raise ValueError("需要确认才能执行批量删除操作")

        try:
            query = Role.query

            # 应用搜索过滤
            if search_filter:
                from sqlalchemy import or_
                query = query.filter(
                    or_(Role.name.contains(search_filter),
                        Role.prompt.contains(search_filter))
                )

            # 获取所有符合条件的角色
            roles_to_delete = query.all()

            # 查找被会话使用的角色ID
            used_role_ids = db.session.query(SessionRole.role_id).distinct().all()
            used_role_ids = {row[0] for row in used_role_ids}

            deleted_roles = 0
            skipped_roles = []
            errors = []

            # 逐个删除角色以确保安全性
            for role in roles_to_delete:
                try:
                    if role.id in used_role_ids:
                        # 角色被使用，跳过删除
                        skipped_roles.append({
                            'id': role.id,
                            'name': role.name,
                            'reason': '角色被会话使用'
                        })
                        continue

                    # 记录删除操作
                    current_app.logger.info(f"批量删除角色: {role.name} (ID: {role.id})")

                    # 删除角色
                    db.session.delete(role)
                    deleted_roles += 1

                except Exception as e:
                    error_msg = f"删除角色 {role.name} 失败: {str(e)}"
                    current_app.logger.error(error_msg)
                    errors.append(error_msg)
                    skipped_roles.append({
                        'id': role.id,
                        'name': role.name,
                        'reason': str(e)
                    })

            # 提交删除操作
            if deleted_roles > 0:
                db.session.commit()
                current_app.logger.info(f"批量删除角色完成: 成功删除 {deleted_roles} 个角色")

            return {
                'deleted_roles': deleted_roles,
                'skipped_roles': skipped_roles,
                'errors': errors
            }

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"批量删除角色失败: {str(e)}")
            raise Exception(f"批量删除角色失败: {str(e)}")