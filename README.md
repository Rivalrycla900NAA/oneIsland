# Charity Pulse Donation Website

**Charity Pulse** is a full-stack donation platform built for the community to give and receive 
with ease. Designed with simplicity and security in mind, it allows users to register, post donations
(like clothes or appliances), comment, and browse available donations—all within a secure and responsive web environment.

---

## Live URL

- **CharityPulse**: [https://charitypulse.azurewebsites.net]

---

## Features

- User Registration and Login  
- Post and Manage Donation Listings  
- Upload Images for Donations  
- Comment System with Nested Replies  
- Secure Authentication using Flask-Login  
- Responsive Frontend with ReactJS  
- Cloud Deployment using Microsoft Azure  

---

## Tech Stack

### Frontend
- ReactJS (Hosted on Azure Static Web Apps)  
- HTML/CSS/JavaScript  

### Backend
- Python Flask (Hosted on Azure App Service)  
- Flask-Login for Authentication  
- Gunicorn as WSGI server  

### Database
- Azure Database for MySQL Flexible Server  

---

## Deployment

The app is deployed using the following Azure services:

| Component     | Service Used                |
|---------------|-----------------------------|
| Frontend      | Azure Static Web Apps       |
| Backend       | Azure App Service (Linux)   |
| Database      | Azure MySQL Flexible Server |
| CI/CD         | GitHub Actions              |

---
