from server import create_application
import travel_backpack.logging

application = create_application()

if __name__ == "__main__":
    application.run()