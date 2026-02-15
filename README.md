# 📚 Study Portal  
### Web-Based Academic Resource Management System

A secure and scalable academic resource management platform built using **Python Flask**, **MongoDB**, and **GridFS**.

---

## 🚀 Project Overview

Study Portal is a role-based web application designed to centralize academic resources for students and administrators.

It allows students to access previous year question papers, study materials, and educational videos in an organized manner, while administrators can securely upload and manage content.

This project demonstrates full-stack development, secure authentication, file handling, and database integration.

---

## 🎯 Problem Statement

In many institutions, academic resources are shared manually via messaging apps or cloud links. This creates:

- Data duplication  
- Unorganized content  
- Security risks  
- Difficulty in searching materials  

Study Portal solves these issues by providing a structured and centralized academic platform.

---

## 🏗️ System Architecture

### Frontend
- HTML5  
- CSS3  
- Bootstrap 5  
- JavaScript  

### Backend
- Python Flask  
- Session-based Authentication  

### Database
- MongoDB  
- GridFS (for storing large PDF files)

---

## 👥 User Roles

### 👨‍🎓 Student
- Register and login securely  
- View study materials  
- View previous year question papers  
- Filter papers by subject, year, and exam type  
- Preview PDFs in browser  
- Download PDFs  
- Watch video lectures  

### 👨‍💼 Admin
- Secure admin login  
- Upload study materials  
- Upload question papers  
- Categorize uploads  
- Edit and delete PDFs  
- Monitor dashboard statistics  
- Track download counts  

---

## 🧩 Core Features

### 🔐 Authentication System
- Password hashing using `werkzeug.security`
- Session-based login
- Role-based access control
- Protected admin routes

### 📤 Admin Upload Module
- Dual upload panels (Study Materials & Question Papers)
- Single backend route handling uploads
- Category-based validation
- File size limit (20MB)
- PDF-only validation

### 📄 Study Mater
