database_schema = """
-- Bus Schedules Table
bus_schedules (
    schedule_id VARCHAR(10) PRIMARY KEY,
    route_id VARCHAR(10) NOT NULL,
    bus_company VARCHAR(50) NOT NULL,
    origin VARCHAR(50) NOT NULL,
    origin_state VARCHAR(50) NOT NULL,
    destination VARCHAR(50) NOT NULL,
    destination_state VARCHAR(50) NOT NULL,
    departure_date DATE NOT NULL,
    departure_time TIME NOT NULL,
    arrival_date DATE NOT NULL,
    arrival_time TIME NOT NULL,
    duration_minutes INTEGER NOT NULL,
    distance_km INTEGER NOT NULL,
    price_naira DECIMAL(10,2) NOT NULL,
    bus_type VARCHAR(20) NOT NULL,
    total_seats INTEGER NOT NULL,
    available_seats INTEGER NOT NULL,
    facilities TEXT,
    intermediate_stops INTEGER
)

-- Bus Routes Table
bus_routes (
    route_id VARCHAR(10) PRIMARY KEY,
    route_name VARCHAR(100) NOT NULL,
    origin_city VARCHAR(50) NOT NULL,
    destination_city VARCHAR(50) NOT NULL,
    distance_km INTEGER NOT NULL,
    estimated_duration_minutes INTEGER NOT NULL,
    is_express BOOLEAN NOT NULL
)

-- Bus Companies Table
bus_companies (
    company_id VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    contact_phone VARCHAR(20),
    contact_email VARCHAR(100),
    website VARCHAR(100),
    rating DECIMAL(3,2)
)

-- Bookings Table
bookings (
    booking_id VARCHAR(20) PRIMARY KEY,
    schedule_id VARCHAR(10) NOT NULL,
    customer_id VARCHAR(20) NOT NULL,
    booking_date TIMESTAMP NOT NULL,
    seat_numbers TEXT NOT NULL,
    num_passengers INTEGER NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    payment_status VARCHAR(20) NOT NULL,
    booking_status VARCHAR(20) NOT NULL
)

-- Customers Table
customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20) NOT NULL,
    address TEXT,
    registration_date TIMESTAMP NOT NULL
)

-- Intermediate Stops Table
intermediate_stops (
    stop_id VARCHAR(20) PRIMARY KEY,
    schedule_id VARCHAR(10) NOT NULL,
    stop_name VARCHAR(50) NOT NULL,
    arrival_time TIME,
    arrival_date DATE,
    duration_from_origin_minutes INTEGER
)
"""