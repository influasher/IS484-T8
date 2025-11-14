from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.recommendation_service import get_client_recommendations
from app.services.portfolio_service import get_client_portfolio_health
from app.services.recommendation_pdf import generate_client_recommendation_report
from app.models.user import User
import os
import threading
import time
import logging
import uuid

recommendations_bp = Blueprint('recommendations', __name__)


def cleanup_old_pdfs():
    """Clean up any old PDF files on startup"""
    try:
        temp_dir = os.path.join(os.path.dirname(__file__), "..", "..", "temp_pdfs")
        if os.path.exists(temp_dir):
            for filename in os.listdir(temp_dir):
                if filename.endswith('.pdf'):
                    filepath = os.path.join(temp_dir, filename)
                    os.remove(filepath)
                    logging.info(f"Cleaned up old PDF file: {filename}")
    except Exception as e:
        logging.error(f"Error cleaning up old PDF files: {e}")


# Clean up old PDFs when the module loads
cleanup_old_pdfs()


def check_client_access(client_id):
    """Helper function to check if current user can access the client data"""
    try:
        # Get current user from JWT token
        current_user_id = get_jwt_identity()
        current_user = User.query.filter(User.id == uuid.UUID(current_user_id)).first()

        if not current_user:
            return None, "User not found"

        # Get the client
        client = User.query.filter(User.id == uuid.UUID(client_id)).first()
        if not client:
            return None, "Client not found"

        # Allow access if:
        # 1. User is an RM and the client is assigned to them
        # 2. User is the client themselves (accessing their own data)
        if current_user.is_rm():
            # Check if the current RM is the client's RM
            if client.rm_id != current_user.id:
                return None, "Access denied. You can only access data for your own clients."
        elif current_user.id == client.id:
            # Client accessing their own data - allowed
            pass
        else:
            return None, "Access denied. You can only access your own data."

        return client, None
    except ValueError:
        return None, "Invalid client ID format"
    except Exception as e:
        return None, f"Authorization error: {str(e)}"


@recommendations_bp.route('/client/<client_id>', methods=['GET'])
@jwt_required()
def get_recommendations(client_id):
    """Get investment recommendations for a specific client"""
    try:
        # Check authorization
        client, error = check_client_access(client_id)
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 401 if "Access denied" in error else 404

        limit = request.args.get('limit', 10, type=int)
        recommendations = get_client_recommendations(client_id, limit)

        return jsonify({
            'success': True,
            'client_id': client_id,
            'recommendations': recommendations,
            'count': len(recommendations)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@recommendations_bp.route('/client/<client_id>/health', methods=['GET'])
@jwt_required()
def get_portfolio_health(client_id):
    """Get portfolio health assessment for a specific client"""
    try:
        # Check authorization
        client, error = check_client_access(client_id)
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 401 if "Access denied" in error else 404

        health_data = get_client_portfolio_health(client_id)

        if 'error' in health_data:
            return jsonify({
                'success': False,
                'error': health_data['error']
            }), 404

        return jsonify({
            'success': True,
            'client_id': client_id,
            'health_data': health_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@recommendations_bp.route('/client/<client_id>/report', methods=['GET'])
@jwt_required()
def get_comprehensive_report(client_id):
    """Get comprehensive report including recommendations and portfolio health"""
    try:
        # Check authorization
        client, error = check_client_access(client_id)
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 401 if "Access denied" in error else 404

        limit = request.args.get('limit', 10, type=int)

        recommendations = get_client_recommendations(client_id, limit)
        health_data = get_client_portfolio_health(client_id)

        if 'error' in health_data:
            return jsonify({
                'success': False,
                'error': health_data['error']
            }), 404

        return jsonify({
            'success': True,
            'client_id': client_id,
            'recommendations': recommendations,
            'health_assessment': health_data,
            'generated_at': None  # Will be set by PDF service
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@recommendations_bp.route('/client/<client_id>/pdf', methods=['GET'])
@jwt_required()
def generate_recommendation_pdf(client_id):
    """Generate and download PDF recommendation report for a client"""
    try:
        # Check authorization
        client, error = check_client_access(client_id)
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 401 if "Access denied" in error else 404

        pdf_filepath = generate_client_recommendation_report(client_id)

        if not os.path.exists(pdf_filepath):
            return jsonify({
                'success': False,
                'error': 'Failed to generate PDF report'
            }), 500

        def cleanup():
            # Wait longer to ensure download completes
            time.sleep(30)
            try:
                if os.path.exists(pdf_filepath):
                    os.remove(pdf_filepath)
                    logging.info(f"Successfully deleted PDF file: {pdf_filepath}")
                else:
                    logging.warning(f"PDF file not found for cleanup: {pdf_filepath}")
            except Exception as e:
                logging.error(f"Error deleting PDF file {pdf_filepath}: {e}")

        # Send the file
        response = send_file(
            pdf_filepath,
            as_attachment=True,
            mimetype="application/pdf"
        )

        # Start cleanup thread
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()
        logging.info(f"Started cleanup thread for PDF: {pdf_filepath}")

        return response

    except Exception as e:
        logging.error(f"Error generating recommendation PDF: {e}")

        # Clean up any partially created PDF file
        try:
            if 'pdf_filepath' in locals() and os.path.exists(pdf_filepath):
                os.remove(pdf_filepath)
                logging.info(f"Cleaned up failed PDF file: {pdf_filepath}")
        except Exception as cleanup_error:
            logging.error(f"Error cleaning up failed PDF: {cleanup_error}")

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500