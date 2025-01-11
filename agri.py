import mysql.connector
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'sirii2812',
    'database': 'agriculture_management'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

class AgricultureManagementHandler(BaseHTTPRequestHandler):
    def _send_response(self, response, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def do_GET(self):
        if self.path.startswith('/farmers'):
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Farmers")
            farmers = cursor.fetchall()
            conn.close()
            self._send_response(farmers)
        
        elif self.path.startswith('/cultivated_area'):
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT f.Farmer_Name, SUM(fi.Area) AS Total_Area
                FROM Farmers f
                JOIN Fields fi ON f.Farmer_ID = fi.Farmer_ID
                GROUP BY f.Farmer_Name
            """)
            areas = cursor.fetchall()
            conn.close()
            self._send_response(areas)

        elif self.path.startswith('/total_harvest'):
            query_components = parse_qs(self.path[13:])  # Extract query parameters
            field_id = query_components.get("field_id", [None])[0]
            if field_id:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT SUM(Harvest_Amount) 
                    FROM Harvest_Records 
                    WHERE Crop_ID IN (SELECT Crop_ID FROM Crops WHERE Field_ID = %s)
                """, (field_id,))
                result = cursor.fetchone()
                conn.close()
                total_harvest = result[0] if result[0] is not None else 0
                self._send_response({"Total_Harvest": total_harvest})

    def do_POST(self):
        if self.path == '/farmers':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            name = data['Farmer_Name']
            contact = data['Contact_Number']
            address = data['Address']

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Farmers (Farmer_Name, Contact_Number, Address) VALUES (%s, %s, %s)",
                (name, contact, address)
            )
            conn.commit()
            conn.close()
            self._send_response({"message": "Farmer added successfully!"}, 201)

def run(server_class=HTTPServer, handler_class=AgricultureManagementHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
