# distributed-booking-system

A **distributed booking system** written in Python for coordinating hotel and band reservations.  

## ✨ Features
- Query hotel and band reservation APIs (RESTful, JSON over HTTP)
- View currently held slots for hotel and band
- View available slots (first 20 hotel/band, first 5 matching slots)
- Reserve the earliest matching slot across both services
- Cancel reservations individually or clean up conflicting bookings
- Automatic retry logic for failed or delayed requests
- Complies with **one request per second** rule
- Handles API unavailability, delays, and concurrency gracefully



## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Dependencies:
  ```bash
  pip install simplejson requests



## 📝 Example Commands
* View held slots → Shows your current reservations
* Reserve earliest slot → Automatically finds & books the earliest available match
* Cancel slot → Removes an unnecessary reservation

### Run the program 

```bash
python3 booking.py

