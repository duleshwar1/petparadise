-- Database Creation
-- (Database is selected automatically via connection string)

-- Drop tables if they exist to ensure clean creation
DROP TABLE IF EXISTS contact;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS pets;
DROP TABLE IF EXISTS users;

-- 1. Users Table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role ENUM('user', 'admin') DEFAULT 'user'
);

-- Index for faster email lookups
CREATE INDEX idx_user_email ON users(email);


-- 2. Pets Table
CREATE TABLE pets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    category ENUM('Dogs', 'Cats', 'Birds', 'Fish') NOT NULL,
    description TEXT,
    image VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster category filtering
CREATE INDEX idx_pet_category ON pets(category);


CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    category ENUM('Food', 'Toys', 'Accessories', 'Grooming') NOT NULL,
    description TEXT,
    image VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster category filtering
CREATE INDEX idx_product_category ON products(category);


-- 4. Orders Table
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    total_price DECIMAL(10, 2) NOT NULL,
    house_no VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    pincode VARCHAR(10) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 5. Order Items Table
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    item_type ENUM('pet', 'product') NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- Indexes for foreign key lookups
CREATE INDEX idx_order_user_id ON orders(user_id);
CREATE INDEX idx_order_product_id ON orders(product_id);


-- 6. Contact Table
CREATE TABLE contact (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    message TEXT NOT NULL
);


-- ==============================================
-- INSERT SAMPLE DATA
-- ==============================================

-- Sample Users (Indian Names)
INSERT INTO users (name, email, password, phone, role) VALUES
('Rahul Sharma', 'rahul@example.in', 'scrypt:32768:8:1$vT0cK9y8$123...', '9876543210', 'user'),
('Priya Verma', 'priya@example.in', 'scrypt:32768:8:1$vT0cK9y8$123...', '9876543211', 'user'),
('Aman Gupta', 'aman@example.in', 'scrypt:32768:8:1$vT0cK9y8$123...', '9876543212', 'user'),
('Admin User', 'admin@petzone.com', 'scrypt:32768:8:1$0nZyR7k1$4fac06180590924040a6e033230b42903f0b2a7e704873130c2c31e21b0689ef', '9999999999', 'admin');

-- Sample Pets (Rupee Prices)
INSERT INTO pets (name, price, category, description, image) VALUES
('Max', 15000.00, 'Dogs', 'An energetic and friendly Golden Retriever puppy.', 'max_golden.png'),
('Luna', 8500.00, 'Cats', 'A playful and cuddly Siamese cat.', 'luna_siamese.png'),
('Charlie', 2500.00, 'Birds', 'A colorful and talkative Macaw.', 'charlie_macaw.png'),
('Bubbles', 500.00, 'Fish', 'A vibrant Betta fish for small aquariums.', 'bubbles_betta.png'),
('Bella', 18000.00, 'Dogs', 'A loyal and protective German Shepherd.', 'bella_gsd.png');

-- Sample Products (Rupee Prices)
INSERT INTO products (name, price, category, description, image) VALUES
('Premium Dog Kibble', 1299.00, 'Food', 'High-protein grain-free formula for adult dogs.', 'dog_kibble.png'),
('Feather Wand Cat Toy', 250.00, 'Toys', 'Interactive toy with natural feathers to keep cats active.', 'cat_wand.png'),
('Orthopedic Pet Bed', 3500.00, 'Accessories', 'Memory foam bed with washable cover for senior pets.', 'pet_bed.png'),
('Flea and Tick Shampoo', 499.00, 'Grooming', 'Medicated shampoo that kills fleas on contact.', 'shampoo.png'),
('Automatic Fish Feeder', 1250.00, 'Accessories', 'Programmed feeder for up to 14 days of holiday feeding.', 'fish_feeder.png');

