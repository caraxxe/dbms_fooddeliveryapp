import mysql.connector
from mysql.connector import Error

def create_foodapp_database():
    """Create the entire foodapp database structure from the provided output"""
    try:
        # Connect to MySQL without specifying database
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='placeholder'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database
            print("Creating database 'foodapp'...")
            cursor.execute("CREATE DATABASE IF NOT EXISTS foodapp")
            cursor.execute("USE foodapp")
            
            # Create tables in correct order to handle foreign key dependencies
            print("\nCreating tables...")
            
            # 1. deliverypartner table (no foreign key dependencies)
            cursor.execute("""
                CREATE TABLE `deliverypartner` (
                  `partner_id` int NOT NULL AUTO_INCREMENT,
                  `name` varchar(100) NOT NULL,
                  `phone` varchar(20) DEFAULT NULL,
                  `rating` decimal(2,1) DEFAULT NULL,
                  PRIMARY KEY (`partner_id`),
                  CONSTRAINT `deliverypartner_chk_1` CHECK ((`rating` between 0 and 5))
                ) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """)
            print("✓ Created table: deliverypartner")
            
            # 2. payment table (no foreign key dependencies)
            cursor.execute("""
                CREATE TABLE `payment` (
                  `pay_id` int NOT NULL AUTO_INCREMENT,
                  `method` varchar(50) NOT NULL,
                  `currency` varchar(10) DEFAULT 'INR',
                  `amount` decimal(10,2) DEFAULT NULL,
                  `status` varchar(30) NOT NULL,
                  PRIMARY KEY (`pay_id`),
                  CONSTRAINT `payment_chk_1` CHECK ((`amount` >= 0))
                ) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """)
            print("✓ Created table: payment")
            
            # 3. user table (depends on payment)
            cursor.execute("""
                CREATE TABLE `user` (
                  `user_id` int NOT NULL AUTO_INCREMENT,
                  `name` varchar(100) NOT NULL,
                  `email` varchar(150) NOT NULL,
                  `address` varchar(255) DEFAULT NULL,
                  `phone` varchar(20) DEFAULT NULL,
                  `pay_id` int DEFAULT NULL,
                  PRIMARY KEY (`user_id`),
                  UNIQUE KEY `email` (`email`),
                  KEY `pay_id` (`pay_id`),
                  CONSTRAINT `user_ibfk_1` FOREIGN KEY (`pay_id`) REFERENCES `payment` (`pay_id`) ON DELETE SET NULL ON UPDATE CASCADE
                ) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """)
            print("✓ Created table: user")
            
            # 4. restaurant table (depends on deliverypartner)
            cursor.execute("""
                CREATE TABLE `restaurant` (
                  `rest_id` int NOT NULL AUTO_INCREMENT,
                  `name` varchar(150) NOT NULL,
                  `address` varchar(255) DEFAULT NULL,
                  `rating` decimal(2,1) DEFAULT NULL,
                  `partner_id` int DEFAULT NULL,
                  PRIMARY KEY (`rest_id`),
                  KEY `partner_id` (`partner_id`),
                  CONSTRAINT `restaurant_ibfk_1` FOREIGN KEY (`partner_id`) REFERENCES `deliverypartner` (`partner_id`) ON DELETE SET NULL ON UPDATE CASCADE,
                  CONSTRAINT `restaurant_chk_1` CHECK ((`rating` between 0 and 5))
                ) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """)
            print("✓ Created table: restaurant")
            
            # 5. orders table (depends on user, deliverypartner, payment)
            cursor.execute("""
                CREATE TABLE `orders` (
                  `order_id` int NOT NULL AUTO_INCREMENT,
                  `order_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  `total_amt` decimal(10,2) DEFAULT NULL,
                  `status` varchar(30) DEFAULT NULL,
                  `user_id` int DEFAULT NULL,
                  `partner_id` int DEFAULT NULL,
                  `pay_id` int DEFAULT NULL,
                  PRIMARY KEY (`order_id`),
                  KEY `user_id` (`user_id`),
                  KEY `partner_id` (`partner_id`),
                  KEY `pay_id` (`pay_id`),
                  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
                  CONSTRAINT `orders_ibfk_2` FOREIGN KEY (`partner_id`) REFERENCES `deliverypartner` (`partner_id`) ON DELETE SET NULL ON UPDATE CASCADE,
                  CONSTRAINT `orders_ibfk_3` FOREIGN KEY (`pay_id`) REFERENCES `payment` (`pay_id`) ON DELETE SET NULL ON UPDATE CASCADE,
                  CONSTRAINT `orders_chk_1` CHECK ((`total_amt` >= 0))
                ) ENGINE=InnoDB AUTO_INCREMENT=46 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """)
            print("✓ Created table: orders")
            
            # 6. menuitem table (depends on restaurant, user)
            cursor.execute("""
                CREATE TABLE `menuitem` (
                  `item_id` int NOT NULL AUTO_INCREMENT,
                  `name` varchar(150) NOT NULL,
                  `price` decimal(10,2) NOT NULL,
                  `quantity` int NOT NULL DEFAULT '1',
                  `rest_id` int DEFAULT NULL,
                  `user_id` int DEFAULT NULL,
                  PRIMARY KEY (`item_id`),
                  KEY `rest_id` (`rest_id`),
                  KEY `user_id` (`user_id`),
                  CONSTRAINT `menuitem_ibfk_1` FOREIGN KEY (`rest_id`) REFERENCES `restaurant` (`rest_id`) ON DELETE CASCADE ON UPDATE CASCADE,
                  CONSTRAINT `menuitem_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`) ON DELETE SET NULL ON UPDATE CASCADE,
                  CONSTRAINT `menuitem_chk_1` CHECK ((`price` > 0)),
                  CONSTRAINT `menuitem_chk_2` CHECK ((`quantity` >= 0))
                ) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """)
            print("✓ Created table: menuitem")
            
            # 7. orderitem table (depends on orders, menuitem)
            cursor.execute("""
                CREATE TABLE `orderitem` (
                  `orderitem_id` int NOT NULL AUTO_INCREMENT,
                  `order_id` int NOT NULL,
                  `item_id` int NOT NULL,
                  `quantity` int NOT NULL,
                  `price` decimal(10,2) NOT NULL,
                  PRIMARY KEY (`orderitem_id`),
                  KEY `order_id` (`order_id`),
                  KEY `item_id` (`item_id`),
                  CONSTRAINT `orderitem_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE,
                  CONSTRAINT `orderitem_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `menuitem` (`item_id`) ON DELETE CASCADE
                ) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """)
            print("✓ Created table: orderitem")
            
            # Create view
            print("\nCreating views...")
            cursor.execute("""
                CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `order_summary_view` AS 
                select `o`.`order_id` AS `order_id`,`o`.`order_date` AS `order_date`,`u`.`name` AS `customer_name`,
                `dp`.`name` AS `delivery_partner`,`r`.`name` AS `restaurant_name`,`o`.`total_amt` AS `order_amount`,
                `p`.`method` AS `payment_method`,`p`.`status` AS `payment_status`,`o`.`status` AS `order_status` 
                from ((((`orders` `o` left join `user` `u` on((`o`.`user_id` = `u`.`user_id`))) 
                left join `deliverypartner` `dp` on((`o`.`partner_id` = `dp`.`partner_id`))) 
                left join `payment` `p` on((`o`.`pay_id` = `p`.`pay_id`))) 
                left join `restaurant` `r` on((`dp`.`partner_id` = `r`.`partner_id`)))
            """)
            print("✓ Created view: order_summary_view")
            
            # Create stored procedures
            print("\nCreating stored procedures...")
            
            # PlaceNewOrder procedure
            cursor.execute("""
                CREATE PROCEDURE `PlaceNewOrder`(
                    IN p_user_id INT,
                    IN p_total_amt DECIMAL(10,2),
                    IN p_method VARCHAR(50)
                )
                BEGIN
                    DECLARE v_pay_id INT;
                    DECLARE v_partner_id INT;

                    -- create payment
                    INSERT INTO payment(method, amount, status)
                    VALUES(p_method, p_total_amt, 'Pending');
                    SET v_pay_id = LAST_INSERT_ID();

                    -- assign random delivery partner
                    SELECT partner_id INTO v_partner_id
                    FROM deliverypartner
                    ORDER BY RAND()
                    LIMIT 1;

                    -- insert order
                    INSERT INTO orders(user_id, partner_id, pay_id, total_amt, status)
                    VALUES(p_user_id, v_partner_id, v_pay_id, p_total_amt, 'Placed');
                END
            """)
            print("✓ Created procedure: PlaceNewOrder")
            
            # UpdateOrderStatus procedure
            cursor.execute("""
                CREATE PROCEDURE `UpdateOrderStatus`(
                    IN p_order_id INT,
                    IN p_new_status VARCHAR(30),
                    IN p_payment_status VARCHAR(30)
                )
                BEGIN
                    UPDATE orders
                    SET status = p_new_status
                    WHERE order_id = p_order_id;

                    UPDATE payment
                    SET status = p_payment_status
                    WHERE pay_id = (SELECT pay_id FROM orders WHERE order_id = p_order_id);
                END
            """)
            print("✓ Created procedure: UpdateOrderStatus")
            
            # Create stored functions
            print("\nCreating stored functions...")
            
            # avg_restaurant_rating function
            cursor.execute("""
                CREATE FUNCTION `avg_restaurant_rating`() RETURNS decimal(3,2)
                DETERMINISTIC
                BEGIN
                    DECLARE avg_rating DECIMAL(3,2);
                    SELECT COALESCE(AVG(rating), 0)
                    INTO avg_rating
                    FROM restaurant;
                    RETURN avg_rating;
                END
            """)
            print("✓ Created function: avg_restaurant_rating")
            
            # total_spent_by_user function
            cursor.execute("""
                CREATE FUNCTION `total_spent_by_user`(uid INT) RETURNS decimal(10,2)
                DETERMINISTIC
                BEGIN
                    DECLARE total DECIMAL(10,2);
                    SELECT COALESCE(SUM(p.amount), 0)
                    INTO total
                    FROM orders o
                    JOIN payment p ON o.pay_id = p.pay_id
                    WHERE o.user_id = uid;
                    RETURN total;
                END
            """)
            print("✓ Created function: total_spent_by_user")
            
            # Create triggers
            print("\nCreating triggers...")
            
            # before_order_insert_create_payment trigger
            cursor.execute("""
                CREATE TRIGGER `before_order_insert_create_payment` BEFORE INSERT ON `orders` FOR EACH ROW 
                BEGIN
                    DECLARE v_pay_id INT;
                    IF NEW.pay_id IS NULL THEN
                        INSERT INTO payment(method, amount, status)
                        VALUES('COD', NEW.total_amt, 'Pending');
                        SET v_pay_id = LAST_INSERT_ID();
                        SET NEW.pay_id = v_pay_id;
                    END IF;
                END
            """)
            print("✓ Created trigger: before_order_insert_create_payment")
            
            # after_order_update_update_partner_rating trigger
            cursor.execute("""
                CREATE TRIGGER `after_order_update_update_partner_rating` AFTER UPDATE ON `orders` FOR EACH ROW 
                BEGIN
                    IF NEW.status = 'Delivered' AND OLD.status <> 'Delivered' THEN
                        UPDATE deliverypartner
                        SET rating = LEAST(5, COALESCE(rating, 3) + 0.1)
                        WHERE partner_id = NEW.partner_id;
                    END IF;
                END
            """)
            print("✓ Created trigger: after_order_update_update_partner_rating")
            
            # Commit all changes
            connection.commit()
            print("\n" + "="*60)
            print("SUCCESS: foodapp database created successfully!")
            print("="*60)
            print("Created: 8 tables, 1 view, 2 procedures, 2 functions, 2 triggers")
            
    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":

    create_foodapp_database()
