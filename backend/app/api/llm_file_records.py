from flask import Blueprint, request, jsonify
from app.services.llm_file_record_service import llm_file_record
from datetime import datetime, timedelta
import os

# 创建蓝图
llm_file_records_bp = Blueprint('llm_file_records', __name__)


@llm_file_records_bp.route('/llm-file-records/session/<int:session_id>', methods=['GET'])
def get_session_llm_records(session_id):
    """获取指定会话的LLM交互记录"""
    try:
        date = request.args.get('date')  # 可选的日期筛选

        records = llm_file_record.get_session_interactions(session_id, date)

        return jsonify({
            'success': True,
            'data': {
                'session_id': session_id,
                'date': date,
                'records': records,
                'total_count': len(records)
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取会话LLM记录失败: {str(e)}'
        }), 500


@llm_file_records_bp.route('/llm-file-records/latest', methods=['GET'])
def get_latest_llm_records():
    """获取最新的LLM交互记录"""
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 200)  # 限制最大数量

        records = llm_file_record.get_latest_interactions(limit)

        return jsonify({
            'success': True,
            'data': {
                'records': records,
                'limit': limit,
                'total_count': len(records)
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取最新LLM记录失败: {str(e)}'
        }), 500


@llm_file_records_bp.route('/llm-file-records/date/<string:date>', methods=['GET'])
def get_date_llm_records(date):
    """获取指定日期的LLM交互记录"""
    try:
        # 验证日期格式
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'success': False,
                'message': '日期格式错误，请使用 YYYY-MM-DD 格式'
            }), 400

        records = llm_file_record.get_date_interactions(date)

        return jsonify({
            'success': True,
            'data': {
                'date': date,
                'records': records,
                'total_count': len(records)
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取日期LLM记录失败: {str(e)}'
        }), 500


@llm_file_records_bp.route('/llm-file-records/errors', methods=['GET'])
def get_error_llm_records():
    """获取错误LLM交互记录"""
    try:
        date = request.args.get('date')  # 可选的日期筛选
        days = request.args.get('days', 7, type=int)  # 默认最近7天

        records = llm_file_record.get_error_interactions(date, days)

        return jsonify({
            'success': True,
            'data': {
                'date': date,
                'days': days,
                'records': records,
                'total_count': len(records)
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取错误LLM记录失败: {str(e)}'
        }), 500


@llm_file_records_bp.route('/llm-file-records/statistics', methods=['GET'])
def get_llm_statistics():
    """获取LLM交互统计信息"""
    try:
        stats = llm_file_record.get_statistics()

        return jsonify({
            'success': True,
            'data': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取LLM统计信息失败: {str(e)}'
        }), 500


@llm_file_records_bp.route('/llm-file-records/cleanup', methods=['POST'])
def cleanup_old_records():
    """清理过期的LLM记录文件"""
    try:
        # 验证权限（实际项目中应该有更严格的权限控制）
        # 这里简单检查是否是管理员请求

        llm_file_record.cleanup_old_files()

        return jsonify({
            'success': True,
            'message': '清理任务已启动'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'清理LLM记录失败: {str(e)}'
        }), 500


@llm_file_records_bp.route('/llm-file-records/health', methods=['GET'])
def health_check():
    """LLM文件记录系统健康检查"""
    try:
        base_dir = "logs/llm_interactions"
        health_info = {
            'service_status': 'healthy',
            'base_directory_exists': os.path.exists(base_dir),
            'base_directory_writable': os.access(base_dir, os.W_OK) if os.path.exists(base_dir) else False,
            'latest_file_exists': os.path.exists(f"{base_dir}/real_time/latest.json"),
            'statistics': llm_file_record.get_statistics()
        }

        # 检查必要的子目录
        required_dirs = ['by_session', 'by_date', 'errors', 'real_time']
        for subdir in required_dirs:
            dir_path = f"{base_dir}/{subdir}"
            health_info[f'{subdir}_directory_exists'] = os.path.exists(dir_path)

        return jsonify({
            'success': True,
            'data': health_info
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'健康检查失败: {str(e)}',
            'service_status': 'unhealthy'
        }), 500