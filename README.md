# Smart Traffic Management System

A web-based AI traffic management system for optimizing traffic flow at intersections.

## Features

- Real-time traffic simulation
- Multiple traffic optimization strategies
- User authentication system
- Admin dashboard with backup/restore functionality
- Secure HTTPS with auto-generated certificates

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/smart-traffic-management.git
   cd smart-traffic-management
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Generate the initial AI model:
   ```
   python generate_model.py
   ```

## Running the Application

1. Start the web server:
   ```
   python main.py
   ```

2. Open your browser and navigate to:
   ```
   https://localhost:5000
   ```

3. Default admin credentials:
   - Email: admin@example.com
   - Password: Admin123

## Security Features

- Password strength requirements
- CSRF protection
- Input validation
- XSS prevention
- Secure session management
- HTTPS with SSL/TLS

## Configuration

Configuration settings are stored in the `config` directory. The system will create this directory and initialize it with default settings on first run.

## License

This project is licensed under the MIT License - see the LICENSE file for details.