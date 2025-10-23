from app import create_app
from app.config import Config

if __name__ == "__main__":
    app = create_app()
    
    # Print all registered routes for debugging
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint}")
    
    app.run(debug=Config.APP_DEBUG, host="0.0.0.0", port=Config.PORT)
# Force rebuild - Thu Oct 23 16:26:05 +08 2025
