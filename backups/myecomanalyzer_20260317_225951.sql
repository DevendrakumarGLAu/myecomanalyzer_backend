-- MySQL dump 10.13  Distrib 8.0.42, for Win64 (x86_64)
--
-- Host: localhost    Database: myecomanalyzer
-- ------------------------------------------------------
-- Server version	8.0.42

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=65 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add user profile',7,'add_userprofile'),(26,'Can change user profile',7,'change_userprofile'),(27,'Can delete user profile',7,'delete_userprofile'),(28,'Can view user profile',7,'view_userprofile'),(29,'Can add platform',8,'add_platform'),(30,'Can change platform',8,'change_platform'),(31,'Can delete platform',8,'delete_platform'),(32,'Can view platform',8,'view_platform'),(33,'Can add category',9,'add_category'),(34,'Can change category',9,'change_category'),(35,'Can delete category',9,'delete_category'),(36,'Can view category',9,'view_category'),(37,'Can add product',10,'add_product'),(38,'Can change product',10,'change_product'),(39,'Can delete product',10,'delete_product'),(40,'Can view product',10,'view_product'),(41,'Can add customer',11,'add_customer'),(42,'Can change customer',11,'change_customer'),(43,'Can delete customer',11,'delete_customer'),(44,'Can view customer',11,'view_customer'),(45,'Can add order',12,'add_order'),(46,'Can change order',12,'change_order'),(47,'Can delete order',12,'delete_order'),(48,'Can view order',12,'view_order'),(49,'Can add order status',13,'add_orderstatus'),(50,'Can change order status',13,'change_orderstatus'),(51,'Can delete order status',13,'delete_orderstatus'),(52,'Can view order status',13,'view_orderstatus'),(53,'Can add marketplace order',14,'add_marketplaceorder'),(54,'Can change marketplace order',14,'change_marketplaceorder'),(55,'Can delete marketplace order',14,'delete_marketplaceorder'),(56,'Can view marketplace order',14,'view_marketplaceorder'),(57,'Can add product variant',15,'add_productvariant'),(58,'Can change product variant',15,'change_productvariant'),(59,'Can delete product variant',15,'delete_productvariant'),(60,'Can view product variant',15,'view_productvariant'),(61,'Can add order settlement',16,'add_ordersettlement'),(62,'Can change order settlement',16,'change_ordersettlement'),(63,'Can delete order settlement',16,'delete_ordersettlement'),(64,'Can view order settlement',16,'view_ordersettlement');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$1000000$DCDIvdXXwqotw5weEjw2y5$FX5lbje3eXICKQJTIV3mjyOeDlQgoUTMonf6zPKJwt0=',NULL,0,'Devendra1997kumar@gmail.com','','','devendra1997kumar@gmail.com',0,1,'2026-03-01 18:14:54.949860');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categories` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `name` varchar(100) NOT NULL,
  `created_by_id` int DEFAULT NULL,
  `deleted_by_id` int DEFAULT NULL,
  `updated_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `categories_created_by_id_05bc8fe3_fk_auth_user_id` (`created_by_id`),
  KEY `categories_deleted_by_id_a21415e4_fk_auth_user_id` (`deleted_by_id`),
  KEY `categories_updated_by_id_2ec4118d_fk_auth_user_id` (`updated_by_id`),
  CONSTRAINT `categories_created_by_id_05bc8fe3_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `categories_deleted_by_id_a21415e4_fk_auth_user_id` FOREIGN KEY (`deleted_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `categories_updated_by_id_2ec4118d_fk_auth_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES (1,1,'2026-03-02 03:00:27.285677','2026-03-02 03:00:27.285677',NULL,'Bangles & Bracelets',1,NULL,NULL);
/*!40000 ALTER TABLE `categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `customers`
--

DROP TABLE IF EXISTS `customers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customers` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `address` longtext NOT NULL,
  `state` varchar(100) NOT NULL,
  `pincode` varchar(10) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `email` varchar(254) DEFAULT NULL,
  `created_by_id` int DEFAULT NULL,
  `deleted_by_id` int DEFAULT NULL,
  `updated_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `customers_created_by_id_3d0160f2_fk_auth_user_id` (`created_by_id`),
  KEY `customers_deleted_by_id_840984e4_fk_auth_user_id` (`deleted_by_id`),
  KEY `customers_updated_by_id_62864352_fk_auth_user_id` (`updated_by_id`),
  CONSTRAINT `customers_created_by_id_3d0160f2_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `customers_deleted_by_id_840984e4_fk_auth_user_id` FOREIGN KEY (`deleted_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `customers_updated_by_id_62864352_fk_auth_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customers`
--

LOCK TABLES `customers` WRITE;
/*!40000 ALTER TABLE `customers` DISABLE KEYS */;
INSERT INTO `customers` VALUES (1,1,'2026-03-09 18:12:48.949570','2026-03-09 18:12:48.949570',NULL,'Unknown','Customer Address COD: Check the payable amount on the app\nsahi Islam\nShadowfax\nnotunmalancha\nMalancha W, Natun Malancha Kali Mandir Nur\nPickup\nMahammad Smriti College Road, Farakka,\nMurshidabad District, Mahadeb Nagar Destination Code\nMahadeb Nagar, West Bengal, 742202 E28_NFK\n_Fara\nIf undelivered, return to:\nDevanjali enterprises\nReturn Code\nSHRI RAM COLONY GALI NA 2, FIROZABAD,\n283203,2627561\nFirozabad\n- SF3074762474FPL\nFirozabad, Uttar Pradesh, 283203\nProduct Details\nSKU Size Qty Color Order No.\n0O0-Z_wu 2.4 1 Pink 259174160814544384_1\nTAX INVOICE Original For Recipient\nBILL TO / SHIP TO Sold by : DEVENDRA KUMAR SINGH\nSahi Islam - notunmalancha, Malancha W, Natun Devanjali enterprises, 23 SHRI RAM COLONY FIROZABAD , Firozabad, Uttar Pradesh, 283203\nMalancha Kali Mandir Nur Mahammad Smriti College GSTIN - 09KICPS3428C1Z4\nRoad, Farakka, Murshidabad District, Mahadeb Nagar ,\nPurchase Order No. Invoice No. Order Date Invoice Date\nMahadeb Nagar, West Bengal, 742202, Place of Supply:\n259174160814544384 fleup261308 28.02.2026 28.02.2026\nWest Bengal\nDescription HSN Qty Gross Amount Discount Taxable Value Taxes Total\nPlastic Cubic Work Bridal\nLook Chooda Set For Women IGST @0.0%\n7018 1 Rs.170.00 Rs.0.00 Rs.170.00 Rs.170.00\nAnd Girls (Pack Of Both Hand Rs.0.00\nChooda Set) - 2.4\nIGST @0.0%\nOther Charges 7018 NA Rs.0.00 Rs.0 Rs.0.00 Rs.0.00\nRs.0.00\nTotal Rs.0.00 Rs.170.00\nTax is not payable on reverse charge basis. This is a computer generated invoice and does not require signature. Other charges are charges that are\napplicable to your order and include charges for logistics fee (where applicable). Includes discounts for your city and/or for online payments (as applicable)','West Bengal','742202',NULL,NULL,1,NULL,1),(2,1,'2026-03-09 18:12:49.510340','2026-03-09 18:12:49.510340',NULL,'Unknown','Customer Address COD: Check the payable amount on the app\nKrishna sharma\nbangraha sitamarhi\nMaha Madhepur Tola, Bajpatti, Sitamarhi Xpress Bees\nDistrict\nPickup\nSitamarhi District, Bihar, 843302\nDestination Code\nIf undelivered, return to:\nE/S-86/4C/302\nDevanjali enterprises\nReturn Code\nSHRI RAM COLONY GALI NA 2, FIROZABAD,\n283203,2627561\nFirozabad\n-\nFirozabad, Uttar Pradesh, 283203 13409639568263\nProduct Details\nSKU Size Qty Color Order No.\n0O0-Z_wu 2.2 1 Pink 259137195763275264_1\nTAX INVOICE Original For Recipient\nBILL TO / SHIP TO Sold by : DEVENDRA KUMAR SINGH\nKrishna Sharma - bangraha sitamarhi , Maha Madhepur Devanjali enterprises, 23 SHRI RAM COLONY FIROZABAD , Firozabad, Uttar Pradesh, 283203\nTola, Bajpatti, Sitamarhi District , Sitamarhi District, GSTIN - 09KICPS3428C1Z4\nBihar, 843302, Place of Supply: Bihar\nPurchase Order No. Invoice No. Order Date Invoice Date\n259137195763275264 fleup261307 28.02.2026 28.02.2026\nDescription HSN Qty Gross Amount Discount Taxable Value Taxes Total\nPlastic Cubic Work Bridal\nLook Chooda Set For Women IGST @0.0%\n7018 1 Rs.168.00 Rs.0.00 Rs.168.00 Rs.168.00\nAnd Girls (Pack Of Both Hand Rs.0.00\nChooda Set) - 2.2\nIGST @0.0%\nOther Charges 7018 NA Rs.0.00 Rs.0 Rs.0.00 Rs.0.00\nRs.0.00\nTotal Rs.0.00 Rs.168.00\nTax is not payable on reverse charge basis. This is a computer generated invoice and does not require signature. Other charges are charges that are\napplicable to your order and include charges for logistics fee (where applicable). Includes discounts for your city and/or for online payments (as applicable)','Bihar','843302',NULL,NULL,1,NULL,1),(3,1,'2026-03-09 18:12:50.022468','2026-03-09 18:12:50.022468',NULL,'Unknown','Customer Address COD: Check the payable amount on the app\nRiya Nayek\nShadowfax\nno\nNAYAK family\nPickup\nBoxitala\nkola ghat, West Bengal, 721641 Destination Code\nE28_GOP\nIf undelivered, return to:\nDevanjali enterprises _Gopi\nSHRI RAM COLONY GALI NA 2, FIROZABAD,\nReturn Code\nFirozabad\n283203,2627561\n-\nFirozabad, Uttar Pradesh, 283203 SF3072822593FPL\nProduct Details\nSKU Size Qty Color Order No.\n0O0-Z_wu 2.6 1 Pink 259265559832532480_1\nTAX INVOICE Original For Recipient\nBILL TO / SHIP TO Sold by : DEVENDRA KUMAR SINGH\nRiya Nayek - no, NAYAK family , Boxitala , kola ghat , Devanjali enterprises, 23 SHRI RAM COLONY FIROZABAD , Firozabad, Uttar Pradesh, 283203\nWest Bengal, 721641, Place of Supply: West Bengal GSTIN - 09KICPS3428C1Z4\nPurchase Order No. Invoice No. Order Date Invoice Date\n259265559832532480 fleup261313 28.02.2026 28.02.2026\nDescription HSN Qty Gross Amount Discount Taxable Value Taxes Total\nPlastic Cubic Work Bridal\nLook Chooda Set For Women IGST @0.0%\n7018 1 Rs.169.00 Rs.0.00 Rs.169.00 Rs.169.00\nAnd Girls (Pack Of Both Hand Rs.0.00\nChooda Set) - 2.6\nIGST @0.0%\nOther Charges 7018 NA Rs.0.00 Rs.0 Rs.0.00 Rs.0.00\nRs.0.00\nTotal Rs.0.00 Rs.169.00\nTax is not payable on reverse charge basis. This is a computer generated invoice and does not require signature. Other charges are charges that are\napplicable to your order and include charges for logistics fee (where applicable). Includes discounts for your city and/or for online payments (as applicable)','West Bengal','721641',NULL,NULL,1,NULL,1),(4,1,'2026-03-09 18:12:50.564834','2026-03-09 18:12:50.564834',NULL,'Unknown','Customer Address COD: Check the payable amount on the app\nddkdjdkd\nShadowfax\nFatou BA chapeau Bara\nBara, Mangrol, Junagadh District\nPickup\nJunagadh District, Gujarat, 362235\nDestination Code\nIf undelivered, return to: W22_MNG\nDevanjali enterprises\nSHRI RAM COLONY GALI NA 2, FIROZABAD, V_Man\nFirozabad\nReturn Code\n-\n283203,2627561\nFirozabad, Uttar Pradesh, 283203\nSF3072964529FPL\nProduct Details\nSKU Size Qty Color Order No.\n0O0-Z_wu 2.6 1 Pink 259441949059702528_1\nTAX INVOICE Original For Recipient\nBILL TO / SHIP TO Sold by : DEVENDRA KUMAR SINGH\nDdkdjdkd - Fatou BA chapeau Bara, Bara, Mangrol, Devanjali enterprises, 23 SHRI RAM COLONY FIROZABAD , Firozabad, Uttar Pradesh, 283203\nJunagadh District , Junagadh District, Gujarat, 362235, GSTIN - 09KICPS3428C1Z4\nPlace of Supply: Gujarat\nPurchase Order No. Invoice No. Order Date Invoice Date\n259441949059702528 fleup261320 01.03.2026 01.03.2026\nDescription HSN Qty Gross Amount Discount Taxable Value Taxes Total\nPlastic Cubic Work Bridal\nLook Chooda Set For Women IGST @0.0%\n7018 1 Rs.169.00 Rs.0.00 Rs.169.00 Rs.169.00\nAnd Girls (Pack Of Both Hand Rs.0.00\nChooda Set) - 2.6\nIGST @0.0%\nOther Charges 7018 NA Rs.0.00 Rs.0 Rs.0.00 Rs.0.00\nRs.0.00\nTotal Rs.0.00 Rs.169.00\nTax is not payable on reverse charge basis. This is a computer generated invoice and does not require signature. Other charges are charges that are\napplicable to your order and include charges for logistics fee (where applicable). Includes discounts for your city and/or for online payments (as applicable)','Gujarat','362235',NULL,NULL,1,NULL,1),(5,1,'2026-03-09 18:12:51.507670','2026-03-09 18:12:51.508311',NULL,'Unknown','Customer Address COD: Check the payable amount on the app\nnam\nShadowfax\nNear Gram Panchayat Office, Nowdihawa\nRoad, Noudhiwa\nPickup\nNowdihawa Road, Noudhiwa, Nautanwa,\nMaharajganj District Destination Code\nMaharajganj District, Uttar Pradesh, 273305 N15_MGZ\n_Nich\nIf undelivered, return to:\nDevanjali enterprises\nReturn Code\nSHRI RAM COLONY GALI NA 2, FIROZABAD,\n283203,2627561\nFirozabad\n- SF3074696794FPL\nFirozabad, Uttar Pradesh, 283203\nProduct Details\nSKU Size Qty Color Order No.\n0O0-Z_wu 2.2 1 Pink 259318205301888448_1\nTAX INVOICE Original For Recipient\nBILL TO / SHIP TO Sold by : DEVENDRA KUMAR SINGH\nNam - Near Gram Panchayat Office, Nowdihawa Road, Devanjali enterprises, 23 SHRI RAM COLONY FIROZABAD , Firozabad, Uttar Pradesh, 283203\nNoudhiwa , Nowdihawa Road, Noudhiwa, Nautanwa, GSTIN - 09KICPS3428C1Z4\nMaharajganj District , Maharajganj District, Uttar\nPurchase Order No. Invoice No. Order Date Invoice Date\nPradesh, 273305, Place of Supply: Uttar Pradesh\n259318205301888448 fleup261316 28.02.2026 28.02.2026\nDescription HSN Qty Gross Amount Discount Taxable Value Taxes Total\nPlastic Cubic Work Bridal\nLook Chooda Set For Women SGST @0.0% :Rs.0.00\n7018 1 Rs.169.00 Rs.4.00 Rs.165.00 Rs.165.00\nAnd Girls (Pack Of Both Hand CGST @0.0% :Rs.0.00\nChooda Set) - 2.2\nSGST @0.0% :Rs.0.00\nOther Charges 7018 NA Rs.0.00 Rs.0 Rs.0.00 Rs.0.00\nCGST @0.0% :Rs.0.00\nTotal Rs.0.00 Rs.165.00\nTax is not payable on reverse charge basis. This is a computer generated invoice and does not require signature. Other charges are charges that are\napplicable to your order and include charges for logistics fee (where applicable). Includes discounts for your city and/or for online payments (as applicable)','Uttar Pradesh','273305',NULL,NULL,1,NULL,1),(6,1,'2026-03-09 18:12:51.982544','2026-03-09 18:12:51.982544',NULL,'Unknown','Customer Address Prepaid: Do not collect cash\nGolu pal\nShadowfax\nJio tavar ke pass\njamaluddin Patti hata Jio tavar ke paas\nPickup\nAzamgarh, Uttar Pradesh, 276124\nDestination Code\nIf undelivered, return to: N15_AMH\nDevanjali enterprises\nSHRI RAM COLONY GALI NA 2, FIROZABAD, _Jiya\nFirozabad\nReturn Code\n-\n283203,2627561\nFirozabad, Uttar Pradesh, 283203\nSF3074674482FPL\nProduct Details\nSKU Size Qty Color Order No.\n0O0-Z_wu 2.4 1 Pink 259327058181592512_1\nTAX INVOICE Original For Recipient\nBILL TO / SHIP TO Sold by : DEVENDRA KUMAR SINGH\nGolu Pal - Jio tavar ke pass , jamaluddin Patti hata Jio Devanjali enterprises, 23 SHRI RAM COLONY FIROZABAD , Firozabad, Uttar Pradesh, 283203\ntavar ke paas , Azamgarh , Uttar Pradesh, 276124, Place GSTIN - 09KICPS3428C1Z4\nof Supply: Uttar Pradesh\nPurchase Order No. Invoice No. Order Date Invoice Date\n259327058181592512 fleup261318 28.02.2026 28.02.2026\nDescription HSN Qty Gross Amount Discount Taxable Value Taxes Total\nPlastic Cubic Work Bridal\nLook Chooda Set For Women SGST @0.0% :Rs.0.00\n7018 1 Rs.168.00 Rs.23.00 Rs.145.00 Rs.145.00\nAnd Girls (Pack Of Both Hand CGST @0.0% :Rs.0.00\nChooda Set) - 2.4\nSGST @0.0% :Rs.0.00\nOther Charges 7018 NA Rs.0.00 Rs.0 Rs.0.00 Rs.0.00\nCGST @0.0% :Rs.0.00\nTotal Rs.0.00 Rs.145.00\nTax is not payable on reverse charge basis. This is a computer generated invoice and does not require signature. Other charges are charges that are\napplicable to your order and include charges for logistics fee (where applicable). Includes discounts for your city and/or for online payments (as applicable)','Uttar Pradesh','276124',NULL,NULL,1,NULL,1),(7,1,'2026-03-09 18:12:52.659349','2026-03-09 18:12:52.660346',NULL,'Unknown','Customer Address Prepaid: Do not collect cash\n6394182620\nShadowfax\nshiv mandir colony new barti bhagwanpur\nvaranasi\nPickup\nshiv mandir colony new basti bhagwanpur\nvaranasi Destination Code\nshiv mandir colony new basti bhagwanpur N16_VNS\nvaranasi\n_Sund\nvaranasi, Uttar Pradesh, 221005\nReturn Code\nIf undelivered, return to:\n283203,2627561\nDevanjali enterprises\nSHRI RAM COLONY GALI NA 2, FIROZABAD, SF3074852334FPL\nFirozabad\n-\nFirozabad, Uttar Pradesh, 283203\nProduct Details\nSKU Size Qty Color Order No.\n0O0-Z_wu 2.8 1 Pink 259348859947291904_1\nTAX INVOICE Original For Recipient\nBILL TO / SHIP TO Sold by : DEVENDRA KUMAR SINGH\n6394182620 - shiv mandir colony new barti bhagwanpur Devanjali enterprises, 23 SHRI RAM COLONY FIROZABAD , Firozabad, Uttar Pradesh, 283203\nvaranasi , shiv mandir colony new basti bhagwanpur GSTIN - 09KICPS3428C1Z4\nvaranasi , shiv mandir colony new basti bhagwanpur\nPurchase Order No. Invoice No. Order Date Invoice Date\nvaranasi , varanasi, Uttar Pradesh, 221005, Place of\n259348859947291904 fleup261319 28.02.2026 28.02.2026\nSupply: Uttar Pradesh\nDescription HSN Qty Gross Amount Discount Taxable Value Taxes Total\nPlastic Cubic Work Bridal\nLook Chooda Set For Women SGST @0.0% :Rs.0.00\n7018 1 Rs.168.00 Rs.21.00 Rs.147.00 Rs.147.00\nAnd Girls (Pack Of Both Hand CGST @0.0% :Rs.0.00\nChooda Set) - 2.8\nSGST @0.0% :Rs.0.00\nOther Charges 7018 NA Rs.0.00 Rs.0 Rs.0.00 Rs.0.00\nCGST @0.0% :Rs.0.00\nTotal Rs.0.00 Rs.147.00\nTax is not payable on reverse charge basis. This is a computer generated invoice and does not require signature. Other charges are charges that are\napplicable to your order and include charges for logistics fee (where applicable). Includes discounts for your city and/or for online payments (as applicable)','Uttar Pradesh','639418',NULL,NULL,1,NULL,1),(8,1,'2026-03-09 18:12:53.134564','2026-03-09 18:12:53.134564',NULL,'Unknown','Customer Address COD: Check the payable amount on the app\nAditi Singh\nnear Ashoka sweets house Valmo Pickup 06/03\nraja vijay pur kothi civil lines mirzapur\nLNF-R0\nAshoka sweets house\nmirzapur, Uttar Pradesh, 231001\nIf undelivered, return to:\nN2/AGRS\nDevanjali enterprises\nSHRI RAM COLONY GALI NA 2, FIROZABAD, N2/VSS\nFirozabad\nB-3/MIR\n-\nFirozabad, Uttar Pradesh, 283203\nVL0083654143879\nProduct Details\nSKU Size Qty Color Order No.\n0O0-Z_wu 2.4 1 Pink 259293265965735680_1\nTAX INVOICE Original For Recipient\nBILL TO / SHIP TO Sold by : DEVENDRA KUMAR SINGH\nAditi Singh - near Ashoka sweets house, raja vijay pur Devanjali enterprises, 23 SHRI RAM COLONY FIROZABAD , Firozabad, Uttar Pradesh, 283203\nkothi civil lines mirzapur , Ashoka sweets house, GSTIN - 09KICPS3428C1Z4\nmirzapur, Uttar Pradesh, 231001, Place of Supply: Uttar\nPurchase Order No. Invoice No. Order Date Invoice Date\nPradesh\n259293265965735680 fleup261314 28.02.2026 28.02.2026\nDescription HSN Qty Gross Amount Discount Taxable Value Taxes Total\nPlastic Cubic Work Bridal\nLook Chooda Set For Women SGST @0.0% :Rs.0.00\n7018 1 Rs.168.00 Rs.4.00 Rs.164.00 Rs.164.00\nAnd Girls (Pack Of Both Hand CGST @0.0% :Rs.0.00\nChooda Set) - 2.4\nSGST @0.0% :Rs.0.00\nOther Charges 7018 NA Rs.0.00 Rs.0 Rs.0.00 Rs.0.00\nCGST @0.0% :Rs.0.00\nTotal Rs.0.00 Rs.164.00\nTax is not payable on reverse charge basis. This is a computer generated invoice and does not require signature. Other charges are charges that are\napplicable to your order and include charges for logistics fee (where applicable). Includes discounts for your city and/or for online payments (as applicable)','Uttar Pradesh','231001',NULL,NULL,1,NULL,1),(9,1,'2026-03-09 18:12:53.598473','2026-03-09 18:12:53.598473',NULL,'Unknown','Customer Address COD: Check the payable amount on the app\ndumpala venkatasubba.ma\nShadowfax\ntakkolu\nmachupalliroad school dhaggara airtel tower\nPickup\nprakkana\nsidhout, Andhra Pradesh, 516002 Destination Code\nS38_HX_\nIf undelivered, return to:\nDevanjali enterprises Jayna\nSHRI RAM COLONY GALI NA 2, FIROZABAD,\nReturn Code\nFirozabad\n283203,2627561\n-\nFirozabad, Uttar Pradesh, 283203 SF3074790628FPL\nProduct Details\nSKU Size Qty Color Order No.\n0O0-Z_wu 2.8 1 Pink 259295970096813376_1\nTAX INVOICE Original For Recipient\nBILL TO / SHIP TO Sold by : DEVENDRA KUMAR SINGH\nDumpala Venkatasubba.ma - takkolu, machupalliroad Devanjali enterprises, 23 SHRI RAM COLONY FIROZABAD , Firozabad, Uttar Pradesh, 283203\nschool dhaggara airtel tower prakkana , sidhout, Andhra GSTIN - 09KICPS3428C1Z4\nPradesh, 516002, Place of Supply: Andhra Pradesh\nPurchase Order No. Invoice No. Order Date Invoice Date\n259295970096813376 fleup261315 28.02.2026 28.02.2026\nDescription HSN Qty Gross Amount Discount Taxable Value Taxes Total\nPlastic Cubic Work Bridal\nLook Chooda Set For Women IGST @0.0%\n7018 1 Rs.167.00 Rs.0.00 Rs.167.00 Rs.167.00\nAnd Girls (Pack Of Both Hand Rs.0.00\nChooda Set) - 2.8\nIGST @0.0%\nOther Charges 7018 NA Rs.0.00 Rs.0 Rs.0.00 Rs.0.00\nRs.0.00\nTotal Rs.0.00 Rs.167.00\nTax is not payable on reverse charge basis. This is a computer generated invoice and does not require signature. Other charges are charges that are\napplicable to your order and include charges for logistics fee (where applicable). Includes discounts for your city and/or for online payments (as applicable)','Andhra Pradesh','516002',NULL,NULL,1,NULL,1),(10,1,'2026-03-09 18:12:54.187732','2026-03-09 18:12:54.187732',NULL,'Unknown','Customer Address COD: Check the payable amount on the app\nPargay tiwari\nShadowfax\nJila Azamgarh gram Lakshman Pur post\nnasiruddinpur petrol pump\nPickup\nlakhamanpur\nAzamgarh, Uttar Pradesh, 276208 Destination Code\nN15_AMH\nIf undelivered, return to:\nDevanjali enterprises _Niza\nSHRI RAM COLONY GALI NA 2, FIROZABAD,\nReturn Code\nFirozabad\n283203,2627561\n-\nFirozabad, Uttar Pradesh, 283203 SF3074661910FPL\nProduct Details\nSKU Size Qty Color Order No.\n0O0-Z_wu 2.6 1 Pink 259226655192317312_1\nTAX INVOICE Original For Recipient\nBILL TO / SHIP TO Sold by : DEVENDRA KUMAR SINGH\nPargay Tiwari - Jila Azamgarh gram Lakshman Pur post Devanjali enterprises, 23 SHRI RAM COLONY FIROZABAD , Firozabad, Uttar Pradesh, 283203\nnasiruddinpur petrol pump , lakhamanpur, Azamgarh, GSTIN - 09KICPS3428C1Z4\nUttar Pradesh, 276208, Place of Supply: Uttar Pradesh\nPurchase Order No. Invoice No. Order Date Invoice Date\n259226655192317312 fleup261311 28.02.2026 28.02.2026\nDescription HSN Qty Gross Amount Discount Taxable Value Taxes Total\nPlastic Cubic Work Bridal\nLook Chooda Set For Women SGST @0.0% :Rs.0.00\n7018 1 Rs.168.00 Rs.4.00 Rs.164.00 Rs.164.00\nAnd Girls (Pack Of Both Hand CGST @0.0% :Rs.0.00\nChooda Set) - 2.6\nSGST @0.0% :Rs.0.00\nOther Charges 7018 NA Rs.0.00 Rs.0 Rs.0.00 Rs.0.00\nCGST @0.0% :Rs.0.00\nTotal Rs.0.00 Rs.164.00\nTax is not payable on reverse charge basis. This is a computer generated invoice and does not require signature. Other charges are charges that are\napplicable to your order and include charges for logistics fee (where applicable). Includes discounts for your city and/or for online payments (as applicable)','Uttar Pradesh','276208',NULL,NULL,1,NULL,1),(11,1,'2026-03-09 18:12:54.670274','2026-03-09 18:12:54.670274',NULL,'Unknown','Customer Address COD: Check the payable amount on the app\nAlahim Sk\nShadowfax\nChandrahat\nChandrahat\nPickup\nLalbagh, West Bengal, 742302\nDestination Code\nIf undelivered, return to: E28_LCA\nDevanjali enterprises\nSHRI RAM COLONY GALI NA 2, FIROZABAD, E_Kal\nFirozabad\nReturn Code\n-\n283203,2627561\nFirozabad, Uttar Pradesh, 283203\nSF3074775058FPL\nProduct Details\nSKU Size Qty Color Order No.\n0O0-Z_wu 2.6 1 Pink 259110181559664000_1\nTAX INVOICE Original For Recipient\nBILL TO / SHIP TO Sold by : DEVENDRA KUMAR SINGH\nAlahim Sk - Chandrahat, Chandrahat, Lalbagh, West Devanjali enterprises, 23 SHRI RAM COLONY FIROZABAD , Firozabad, Uttar Pradesh, 283203\nBengal, 742302, Place of Supply: West Bengal GSTIN - 09KICPS3428C1Z4\nPurchase Order No. Invoice No. Order Date Invoice Date\n259110181559664000 fleup261305 28.02.2026 28.02.2026\nDescription HSN Qty Gross Amount Discount Taxable Value Taxes Total\nPlastic Cubic Work Bridal\nLook Chooda Set For Women IGST @0.0%\n7018 1 Rs.167.00 Rs.0.00 Rs.167.00 Rs.167.00\nAnd Girls (Pack Of Both Hand Rs.0.00\nChooda Set) - 2.6\nIGST @0.0%\nOther Charges 7018 NA Rs.0.00 Rs.0 Rs.0.00 Rs.0.00\nRs.0.00\nTotal Rs.0.00 Rs.167.00\nTax is not payable on reverse charge basis. This is a computer generated invoice and does not require signature. Other charges are charges that are\napplicable to your order and include charges for logistics fee (where applicable). Includes discounts for your city and/or for online payments (as applicable)','West Bengal','742302',NULL,NULL,1,NULL,1),(12,1,'2026-03-09 18:12:55.131700','2026-03-09 18:12:55.131700',NULL,'Unknown','Customer Address COD: Check the payable amount on the app\nPrakash Behera\nSanasirai pur Valmo Pickup 07/03\nadua sahi primary school road\nLNF-R0\nbanpur, Odisha, 752031\nIf undelivered, return to:\nDevanjali enterprises\nN2/AGRS\nSHRI RAM COLONY GALI NA 2, FIROZABAD,\nFirozabad E2/BUS\n-\n3/VEG\nFirozabad, Uttar Pradesh, 283203\nVL0083654141150\nProduct Details\nSKU Size Qty Color Order No.\n0O0-Z_wu 2.6 1 Pink 259133708752977280_1\nTAX INVOICE Original For Recipient\nBILL TO / SHIP TO Sold by : DEVENDRA KUMAR SINGH\nPrakash Behera - Sanasirai pur, adua sahi primary Devanjali enterprises, 23 SHRI RAM COLONY FIROZABAD , Firozabad, Uttar Pradesh, 283203\nschool road , banpur, Odisha, 752031, Place of Supply: GSTIN - 09KICPS3428C1Z4\nOdisha\nPurchase Order No. Invoice No. Order Date Invoice Date\n259133708752977280 fleup261306 28.02.2026 28.02.2026\nDescription HSN Qty Gross Amount Discount Taxable Value Taxes Total\nPlastic Cubic Work Bridal\nLook Chooda Set For Women IGST @0.0%\n7018 1 Rs.170.00 Rs.0.00 Rs.170.00 Rs.170.00\nAnd Girls (Pack Of Both Hand Rs.0.00\nChooda Set) - 2.6\nIGST @0.0%\nOther Charges 7018 NA Rs.0.00 Rs.0 Rs.0.00 Rs.0.00\nRs.0.00\nTotal Rs.0.00 Rs.170.00\nTax is not payable on reverse charge basis. This is a computer generated invoice and does not require signature. Other charges are charges that are\napplicable to your order and include charges for logistics fee (where applicable). Includes discounts for your city and/or for online payments (as applicable)','Odisha','752031',NULL,NULL,1,NULL,1);
/*!40000 ALTER TABLE `customers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(9,'categories','category'),(5,'contenttypes','contenttype'),(11,'customers','customer'),(14,'marketplace','marketplaceorder'),(12,'orders','order'),(13,'orders_status','orderstatus'),(16,'payments','ordersettlement'),(8,'platforms','platform'),(10,'products','product'),(15,'products','productvariant'),(6,'sessions','session'),(7,'users','userprofile');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-03-01 18:13:16.566060'),(2,'auth','0001_initial','2026-03-01 18:13:17.516302'),(3,'admin','0001_initial','2026-03-01 18:13:17.734301'),(4,'admin','0002_logentry_remove_auto_add','2026-03-01 18:13:17.740864'),(5,'admin','0003_logentry_add_action_flag_choices','2026-03-01 18:13:17.756713'),(6,'contenttypes','0002_remove_content_type_name','2026-03-01 18:13:17.925041'),(7,'auth','0002_alter_permission_name_max_length','2026-03-01 18:13:18.023921'),(8,'auth','0003_alter_user_email_max_length','2026-03-01 18:13:18.066905'),(9,'auth','0004_alter_user_username_opts','2026-03-01 18:13:18.083289'),(10,'auth','0005_alter_user_last_login_null','2026-03-01 18:13:18.175433'),(11,'auth','0006_require_contenttypes_0002','2026-03-01 18:13:18.180470'),(12,'auth','0007_alter_validators_add_error_messages','2026-03-01 18:13:18.187109'),(13,'auth','0008_alter_user_username_max_length','2026-03-01 18:13:18.295811'),(14,'auth','0009_alter_user_last_name_max_length','2026-03-01 18:13:18.434746'),(15,'auth','0010_alter_group_name_max_length','2026-03-01 18:13:18.563930'),(16,'auth','0011_update_proxy_permissions','2026-03-01 18:13:18.591838'),(17,'auth','0012_alter_user_first_name_max_length','2026-03-01 18:13:18.813634'),(18,'categories','0001_initial','2026-03-01 18:13:19.235173'),(19,'customers','0001_initial','2026-03-01 18:13:19.667372'),(20,'platforms','0001_initial','2026-03-01 18:13:20.411160'),(21,'marketplace','0001_initial','2026-03-01 18:13:20.919033'),(22,'products','0001_initial','2026-03-01 18:13:21.511925'),(23,'orders_status','0001_initial','2026-03-01 18:13:21.798156'),(24,'orders','0001_initial','2026-03-01 18:13:22.394476'),(25,'sessions','0001_initial','2026-03-01 18:13:22.445148'),(26,'users','0001_initial','2026-03-01 18:13:22.577473'),(27,'products','0002_remove_product_color_and_more','2026-03-02 17:15:41.626537'),(28,'products','0003_product_commission_percent_product_gst_percent_and_more','2026-03-06 03:52:51.973459'),(29,'products','0004_productvariant_rto_cost_productvariant_shipping_cost','2026-03-08 03:58:17.094943'),(30,'products','0005_alter_productvariant_sku','2026-03-09 18:45:25.465768'),(31,'payments','0001_initial','2026-03-10 18:33:58.160183'),(32,'payments','0002_alter_ordersettlement_table','2026-03-12 18:28:19.979118');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `marketplace_orders`
--

DROP TABLE IF EXISTS `marketplace_orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `marketplace_orders` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `marketplace_order_id` varchar(120) NOT NULL,
  `order_date` date NOT NULL,
  `created_by_id` int DEFAULT NULL,
  `customer_id` bigint NOT NULL,
  `deleted_by_id` int DEFAULT NULL,
  `platform_id` bigint NOT NULL,
  `updated_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `marketplace_orders_platform_id_marketplace__87a8ab58_uniq` (`platform_id`,`marketplace_order_id`),
  KEY `marketplace_orders_created_by_id_dc2946a9_fk_auth_user_id` (`created_by_id`),
  KEY `marketplace_orders_customer_id_147cb9a4_fk_customers_id` (`customer_id`),
  KEY `marketplace_orders_deleted_by_id_0811caed_fk_auth_user_id` (`deleted_by_id`),
  KEY `marketplace_orders_updated_by_id_e3d0062b_fk_auth_user_id` (`updated_by_id`),
  KEY `marketplace_platfor_65615c_idx` (`platform_id`,`marketplace_order_id`),
  KEY `marketplace_order_d_7af7a7_idx` (`order_date`),
  CONSTRAINT `marketplace_orders_created_by_id_dc2946a9_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `marketplace_orders_customer_id_147cb9a4_fk_customers_id` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`),
  CONSTRAINT `marketplace_orders_deleted_by_id_0811caed_fk_auth_user_id` FOREIGN KEY (`deleted_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `marketplace_orders_platform_id_4fb8b3a5_fk_platforms_id` FOREIGN KEY (`platform_id`) REFERENCES `platforms` (`id`),
  CONSTRAINT `marketplace_orders_updated_by_id_e3d0062b_fk_auth_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `marketplace_orders`
--

LOCK TABLES `marketplace_orders` WRITE;
/*!40000 ALTER TABLE `marketplace_orders` DISABLE KEYS */;
INSERT INTO `marketplace_orders` VALUES (1,1,'2026-03-09 18:12:49.049259','2026-03-09 18:12:49.049259',NULL,'259174160814544384','2026-02-28',1,1,NULL,2,1),(2,1,'2026-03-09 18:12:49.521460','2026-03-09 18:12:49.521460',NULL,'259137195763275264','2026-02-28',1,2,NULL,2,1),(3,1,'2026-03-09 18:12:50.035564','2026-03-09 18:12:50.035564',NULL,'259265559832532480','2026-02-28',1,3,NULL,2,1),(4,1,'2026-03-09 18:12:50.574845','2026-03-09 18:12:50.574845',NULL,'259441949059702528','2026-03-01',1,4,NULL,2,1),(5,1,'2026-03-09 18:12:51.518940','2026-03-09 18:12:51.518940',NULL,'259318205301888448','2026-02-28',1,5,NULL,2,1),(6,1,'2026-03-09 18:12:51.991210','2026-03-09 18:12:51.991210',NULL,'259327058181592512','2026-02-28',1,6,NULL,2,1),(7,1,'2026-03-09 18:12:52.670055','2026-03-09 18:12:52.670097',NULL,'259348859947291904','2026-02-28',1,7,NULL,2,1),(8,1,'2026-03-09 18:12:53.144391','2026-03-09 18:12:53.144391',NULL,'259293265965735680','2026-02-28',1,8,NULL,2,1),(9,1,'2026-03-09 18:12:53.608715','2026-03-09 18:12:53.608715',NULL,'259295970096813376','2026-02-28',1,9,NULL,2,1),(10,1,'2026-03-09 18:12:54.204800','2026-03-09 18:12:54.204800',NULL,'259226655192317312','2026-02-28',1,10,NULL,2,1),(11,1,'2026-03-09 18:12:54.681018','2026-03-09 18:12:54.681018',NULL,'259110181559664000','2026-02-28',1,11,NULL,2,1),(12,1,'2026-03-09 18:12:55.143616','2026-03-09 18:12:55.143616',NULL,'259133708752977280','2026-02-28',1,12,NULL,2,1);
/*!40000 ALTER TABLE `marketplace_orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `meesho_order_settlements`
--

DROP TABLE IF EXISTS `meesho_order_settlements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `meesho_order_settlements` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `transaction_id` varchar(120) NOT NULL,
  `payment_date` date NOT NULL,
  `total_sale_amount` double NOT NULL,
  `total_return_amount` double NOT NULL,
  `final_settlement_amount` double NOT NULL,
  `fixed_fee` double NOT NULL,
  `warehousing_fee` double NOT NULL,
  `return_premium` double NOT NULL,
  `return_premium_return` double NOT NULL,
  `gst_percent` decimal(5,2) NOT NULL,
  `created_by_id` int DEFAULT NULL,
  `deleted_by_id` int DEFAULT NULL,
  `order_id` bigint NOT NULL,
  `updated_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `order_id` (`order_id`),
  KEY `order_settlements_created_by_id_62083a57_fk_auth_user_id` (`created_by_id`),
  KEY `order_settlements_deleted_by_id_db0787d7_fk_auth_user_id` (`deleted_by_id`),
  KEY `order_settlements_updated_by_id_fc191320_fk_auth_user_id` (`updated_by_id`),
  CONSTRAINT `order_settlements_created_by_id_62083a57_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `order_settlements_deleted_by_id_db0787d7_fk_auth_user_id` FOREIGN KEY (`deleted_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `order_settlements_order_id_5f2b3f7f_fk_orders_id` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`),
  CONSTRAINT `order_settlements_updated_by_id_fc191320_fk_auth_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `meesho_order_settlements`
--

LOCK TABLES `meesho_order_settlements` WRITE;
/*!40000 ALTER TABLE `meesho_order_settlements` DISABLE KEYS */;
/*!40000 ALTER TABLE `meesho_order_settlements` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_status`
--

DROP TABLE IF EXISTS `order_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order_status` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `code` varchar(50) NOT NULL,
  `label` varchar(100) NOT NULL,
  `created_by_id` int DEFAULT NULL,
  `deleted_by_id` int DEFAULT NULL,
  `updated_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `order_status_created_by_id_5edac4db_fk_auth_user_id` (`created_by_id`),
  KEY `order_status_deleted_by_id_ae1186d5_fk_auth_user_id` (`deleted_by_id`),
  KEY `order_status_updated_by_id_4389cb67_fk_auth_user_id` (`updated_by_id`),
  CONSTRAINT `order_status_created_by_id_5edac4db_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `order_status_deleted_by_id_ae1186d5_fk_auth_user_id` FOREIGN KEY (`deleted_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `order_status_updated_by_id_4389cb67_fk_auth_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_status`
--

LOCK TABLES `order_status` WRITE;
/*!40000 ALTER TABLE `order_status` DISABLE KEYS */;
INSERT INTO `order_status` VALUES (1,1,'2026-03-03 00:15:27.000000','2026-03-03 00:15:27.000000',NULL,'RTO_COMPLETE','RTO Complete',1,NULL,NULL),(2,1,'2026-03-03 00:15:27.000000','2026-03-03 00:15:27.000000',NULL,'CANCELLED','Cancelled',1,NULL,NULL),(3,1,'2026-03-03 00:15:27.000000','2026-03-03 00:15:27.000000',NULL,'DELIVERED','Delivered',1,NULL,NULL),(4,1,'2026-03-03 00:15:27.000000','2026-03-03 00:15:27.000000',NULL,'DOOR_STEP_EXCHANGED','Door Step Exchanged',1,NULL,NULL),(5,1,'2026-03-03 00:15:27.000000','2026-03-03 00:15:27.000000',NULL,'LOST','Lost',1,NULL,NULL),(6,1,'2026-03-09 18:05:52.540182','2026-03-09 18:05:52.547683',NULL,'PLACED','Placed',1,NULL,1);
/*!40000 ALTER TABLE `order_status` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orders` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `marketplace_sub_order_id` varchar(120) NOT NULL,
  `quantity` int NOT NULL,
  `selling_price` double NOT NULL,
  `created_by_id` int DEFAULT NULL,
  `deleted_by_id` int DEFAULT NULL,
  `marketplace_order_id` bigint NOT NULL,
  `product_id` bigint NOT NULL,
  `status_id` bigint NOT NULL,
  `updated_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `orders_marketplace_order_id_mar_d1827734_uniq` (`marketplace_order_id`,`marketplace_sub_order_id`),
  KEY `orders_created_by_id_b9de303d_fk_auth_user_id` (`created_by_id`),
  KEY `orders_deleted_by_id_48ac0725_fk_auth_user_id` (`deleted_by_id`),
  KEY `orders_product_id_410f7af4_fk_products_id` (`product_id`),
  KEY `orders_status_id_e763064e_fk_order_status_id` (`status_id`),
  KEY `orders_updated_by_id_04a74b30_fk_auth_user_id` (`updated_by_id`),
  KEY `orders_marketp_56a33f_idx` (`marketplace_sub_order_id`),
  CONSTRAINT `orders_created_by_id_b9de303d_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `orders_deleted_by_id_48ac0725_fk_auth_user_id` FOREIGN KEY (`deleted_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `orders_marketplace_order_id_87a67b3c_fk_marketplace_orders_id` FOREIGN KEY (`marketplace_order_id`) REFERENCES `marketplace_orders` (`id`),
  CONSTRAINT `orders_product_id_410f7af4_fk_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `orders_status_id_e763064e_fk_order_status_id` FOREIGN KEY (`status_id`) REFERENCES `order_status` (`id`),
  CONSTRAINT `orders_updated_by_id_04a74b30_fk_auth_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
INSERT INTO `orders` VALUES (1,1,'2026-03-09 18:12:49.063896','2026-03-09 18:12:49.063896',NULL,'259174160814544384_1',1,170,1,NULL,1,1,6,1),(2,1,'2026-03-09 18:12:49.527141','2026-03-09 18:12:49.527141',NULL,'259137195763275264_1',1,168,1,NULL,2,1,6,1),(3,1,'2026-03-09 18:12:50.041554','2026-03-09 18:12:50.041554',NULL,'259265559832532480_1',1,169,1,NULL,3,1,6,1),(4,1,'2026-03-09 18:12:50.579786','2026-03-09 18:12:50.579786',NULL,'259441949059702528_1',1,169,1,NULL,4,1,6,1),(5,1,'2026-03-09 18:12:51.527173','2026-03-09 18:12:51.527173',NULL,'259318205301888448_1',1,165,1,NULL,5,1,6,1),(6,1,'2026-03-09 18:12:51.997351','2026-03-09 18:12:51.997351',NULL,'259327058181592512_1',1,145,1,NULL,6,1,6,1),(7,1,'2026-03-09 18:12:52.675559','2026-03-09 18:12:52.675559',NULL,'259348859947291904_1',1,147,1,NULL,7,1,6,1),(8,1,'2026-03-09 18:12:53.154132','2026-03-09 18:12:53.154132',NULL,'259293265965735680_1',1,164,1,NULL,8,1,6,1),(9,1,'2026-03-09 18:12:53.610708','2026-03-09 18:12:53.610708',NULL,'259295970096813376_1',1,167,1,NULL,9,1,6,1),(10,1,'2026-03-09 18:12:54.210952','2026-03-09 18:12:54.210952',NULL,'259226655192317312_1',1,164,1,NULL,10,1,6,1),(11,1,'2026-03-09 18:12:54.687045','2026-03-09 18:12:54.687045',NULL,'259110181559664000_1',1,167,1,NULL,11,1,6,1),(12,1,'2026-03-09 18:12:55.151361','2026-03-09 18:12:55.151361',NULL,'259133708752977280_1',1,170,1,NULL,12,1,6,1);
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `platforms`
--

DROP TABLE IF EXISTS `platforms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `platforms` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `name` varchar(100) NOT NULL,
  `code` varchar(50) NOT NULL,
  `created_by_id` int DEFAULT NULL,
  `deleted_by_id` int DEFAULT NULL,
  `updated_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `code` (`code`),
  KEY `platforms_created_by_id_05f719db_fk_auth_user_id` (`created_by_id`),
  KEY `platforms_deleted_by_id_5cd486d0_fk_auth_user_id` (`deleted_by_id`),
  KEY `platforms_updated_by_id_60f1675c_fk_auth_user_id` (`updated_by_id`),
  CONSTRAINT `platforms_created_by_id_05f719db_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `platforms_deleted_by_id_5cd486d0_fk_auth_user_id` FOREIGN KEY (`deleted_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `platforms_updated_by_id_60f1675c_fk_auth_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `platforms`
--

LOCK TABLES `platforms` WRITE;
/*!40000 ALTER TABLE `platforms` DISABLE KEYS */;
INSERT INTO `platforms` VALUES (1,1,'2026-03-03 00:19:05.000000','2026-03-03 00:19:05.000000',NULL,'Flipkart','FLIPKART',1,NULL,NULL),(2,1,'2026-03-03 00:19:05.000000','2026-03-03 00:19:05.000000',NULL,'Meesho','MEESHO',1,NULL,NULL),(3,1,'2026-03-03 00:19:05.000000','2026-03-03 00:19:05.000000',NULL,'Amazon','AMAZON',1,NULL,NULL);
/*!40000 ALTER TABLE `platforms` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_variants`
--

DROP TABLE IF EXISTS `product_variants`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `product_variants` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `sku` varchar(50) NOT NULL,
  `size` varchar(50) DEFAULT NULL,
  `color` varchar(50) DEFAULT NULL,
  `cost_price` double NOT NULL,
  `selling_price` double NOT NULL,
  `stock` int NOT NULL,
  `product_id` bigint NOT NULL,
  `rto_cost` double NOT NULL,
  `shipping_cost` double NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `product_variants_product_id_size_color_52f9365c_uniq` (`product_id`,`size`,`color`),
  CONSTRAINT `product_variants_product_id_019d9f04_fk_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_variants`
--

LOCK TABLES `product_variants` WRITE;
/*!40000 ALTER TABLE `product_variants` DISABLE KEYS */;
INSERT INTO `product_variants` VALUES (25,'3tzqEH74','2.2','PINK',52,100,123,10,10,100),(26,'3tzqEH74','2.4','PINK',52,100,10,10,10,100),(27,'3tzqEH74','2.6','PINK',52,100,10,10,10,100),(28,'3tzqEH74','2.8','PINK',52,100,10,10,10,100),(29,'Dj8jFywr','2.2','WHITE',30,100,11,2,10,100),(30,'Dj8jFywr','2.4','WHITE',30,100,10,2,10,100),(31,'Dj8jFywr','2.6','WHITE',30,100,10,2,10,100),(32,'Dj8jFywr','2.8','WHITE',30,100,10,2,10,100),(33,'0O0-Z_wu','2.2','PINK',52,112,14,1,12,100),(34,'0O0-Z_wu','2.4','PINK',52,112,12,1,12,100),(35,'0O0-Z_wu','2.6','PINK',52,112,12,1,12,100),(36,'0O0-Z_wu','2.8','PINK',52,112,12,1,12,100);
/*!40000 ALTER TABLE `product_variants` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `products` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `catalog_id` varchar(50) NOT NULL,
  `name` varchar(255) NOT NULL,
  `category_id` bigint NOT NULL,
  `created_by_id` int DEFAULT NULL,
  `deleted_by_id` int DEFAULT NULL,
  `owner_id` int NOT NULL,
  `updated_by_id` int DEFAULT NULL,
  `commission_percent` decimal(5,2) NOT NULL,
  `gst_percent` decimal(5,2) NOT NULL,
  `platform_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `catalog_id` (`catalog_id`),
  KEY `products_category_id_a7a3a156_fk_categories_id` (`category_id`),
  KEY `products_created_by_id_924ff91a_fk_auth_user_id` (`created_by_id`),
  KEY `products_deleted_by_id_e4330cc2_fk_auth_user_id` (`deleted_by_id`),
  KEY `products_owner_id_13ed5e13_fk_auth_user_id` (`owner_id`),
  KEY `products_updated_by_id_65dc5679_fk_auth_user_id` (`updated_by_id`),
  KEY `products_platform_id_6738346f_fk_platforms_id` (`platform_id`),
  CONSTRAINT `products_category_id_a7a3a156_fk_categories_id` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`),
  CONSTRAINT `products_created_by_id_924ff91a_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `products_deleted_by_id_e4330cc2_fk_auth_user_id` FOREIGN KEY (`deleted_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `products_owner_id_13ed5e13_fk_auth_user_id` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `products_platform_id_6738346f_fk_platforms_id` FOREIGN KEY (`platform_id`) REFERENCES `platforms` (`id`),
  CONSTRAINT `products_updated_by_id_65dc5679_fk_auth_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products`
--

LOCK TABLES `products` WRITE;
/*!40000 ALTER TABLE `products` DISABLE KEYS */;
INSERT INTO `products` VALUES (1,1,'2026-03-06 03:26:28.647175','2026-03-09 18:50:33.571367',NULL,'317373503','Plastic Cubic Work Bridal Look Chooda Set For Women And Girls (Pack Of Both Hand Chooda Set)',1,1,NULL,1,1,10.00,10.00,2),(2,1,'2026-03-08 04:49:02.419940','2026-03-09 18:50:01.488447',NULL,'240146022','Devanjali plastic bangles with AmericanDiamond',1,1,NULL,1,1,0.00,0.00,2),(10,1,'2026-03-09 18:45:47.456778','2026-03-09 18:45:47.456778',NULL,'233684460','Devanajali chooda set with cubic ziconia work for women arts and Girls (Pack of Both Hand Chooda Set)',1,1,NULL,1,1,0.00,0.00,2);
/*!40000 ALTER TABLE `products` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_profile`
--

DROP TABLE IF EXISTS `user_profile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_profile` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `first_name` varchar(150) DEFAULT NULL,
  `last_name` varchar(150) DEFAULT NULL,
  `mobile_number` varchar(20) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `trial_start` datetime(6) DEFAULT NULL,
  `trial_end` datetime(6) DEFAULT NULL,
  `subscription_start` datetime(6) DEFAULT NULL,
  `subscription_end` datetime(6) DEFAULT NULL,
  `payment_verified` tinyint(1) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `user_profile_user_id_8fdce8e2_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_profile`
--

LOCK TABLES `user_profile` WRITE;
/*!40000 ALTER TABLE `user_profile` DISABLE KEYS */;
INSERT INTO `user_profile` VALUES (1,'Devendra','Kumar','07351864609','devendra1997kumar@gmail.com',1,'2026-03-01 18:14:55.790774','2026-03-01 18:14:55.794042','2026-03-08 18:14:55.794042',NULL,NULL,0,1);
/*!40000 ALTER TABLE `user_profile` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-03-17 22:59:52
