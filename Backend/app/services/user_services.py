from sqlalchemy import func, or_
from app.models.user import User, UserRole
from app import db


def search_users(query, page=1, per_page=20, role_filter='client'):
    """
    Search users with full-text search functionality.
    
    Args:
        query (str): Search query string
        page (int): Page number for pagination
        per_page (int): Number of results per page
        role_filter (str): Filter by role ('client', 'relationship_manager', or 'all')
    
    Returns:
        dict: Contains users list, pagination info, and search metadata
    """
    try:
        # Base query for users
        user_query = User.query
        
        # Apply role filter
        if role_filter == 'client':
            user_query = user_query.filter(User.role == UserRole.CLIENT)
        elif role_filter == 'relationship_manager':
            user_query = user_query.filter(User.role == UserRole.RELATIONSHIP_MANAGER)
        # 'all' means no role filter
        
        # Apply search filter if query is provided
        if query and query.strip():
            search_term = f"%{query.strip()}%"
            user_query = user_query.filter(
                or_(
                    User.username.ilike(search_term),
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    func.concat(User.first_name, ' ', User.last_name).ilike(search_term)
                )
            )
        
        # Apply pagination
        paginated_users = user_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Format users data
        users = []
        for user in paginated_users.items:
            users.append({
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": f"{user.first_name} {user.last_name}",
                "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                "rm_id": str(user.rm_id) if user.rm_id else None,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            })
        
        return {
            "users": users,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": paginated_users.total,
                "pages": paginated_users.pages,
                "has_next": paginated_users.has_next,
                "has_prev": paginated_users.has_prev
            },
            "search_query": query,
            "role_filter": role_filter
        }
        
    except Exception as e:
        raise Exception(f"User search failed: {str(e)}")


def get_all_clients(page=1, per_page=20):
    """
    Get all clients with pagination.
    
    Args:
        page (int): Page number for pagination
        per_page (int): Number of results per page
    
    Returns:
        dict: Contains clients list and pagination info
    """
    return search_users(query="", page=page, per_page=per_page, role_filter='client')


def get_client_by_id(client_id):
    """
    Get a specific client by ID.
    
    Args:
        client_id: The client's ID
    
    Returns:
        dict: Client data or None if not found
    """
    try:
        user = User.query.filter_by(id=client_id, role=UserRole.CLIENT).first()
        
        if not user:
            return None
            
        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": f"{user.first_name} {user.last_name}",
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "rm_id": str(user.rm_id) if user.rm_id else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        
    except Exception as e:
        raise Exception(f"Failed to get client: {str(e)}")
