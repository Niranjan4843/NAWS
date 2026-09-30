/* -------------------------------------------------------------
   MOVIE MAGIC - INTERACTIVE JAVASCRIPT & SEAT BOOKING ENGINE
   ------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
  initSeatPicker();
  initAutoDismissAlerts();
  checkUserNotifications();
});

// ------------------ SEAT SELECTION ENGINE ------------------
let selectedSeats = [];

function initSeatPicker() {
  const seatGrid = document.getElementById('seatGrid');
  if (!seatGrid) return;

  const seats = seatGrid.querySelectorAll('.seat.available');
  const countElement = document.getElementById('selectedCount');
  const seatsListElement = document.getElementById('selectedSeatsList');
  const totalPriceElement = document.getElementById('totalPrice');
  const bookBtn = document.getElementById('confirmBookingBtn');

  const unitPrice = parseFloat(seatGrid.dataset.unitPrice || "15.00");

  seats.forEach(seat => {
    seat.addEventListener('click', () => {
      const seatId = seat.dataset.seatId;

      if (seat.classList.contains('selected')) {
        seat.classList.remove('selected');
        selectedSeats = selectedSeats.filter(id => id !== seatId);
      } else {
        seat.classList.add('selected');
        selectedSeats.push(seatId);
      }

      // Update UI displays
      const count = selectedSeats.length;
      if (countElement) countElement.textContent = count;
      if (seatsListElement) {
        seatsListElement.textContent = count > 0 ? selectedSeats.join(', ') : 'None';
      }
      if (totalPriceElement) {
        totalPriceElement.textContent = (count * unitPrice).toFixed(2);
      }

      if (bookBtn) {
        bookBtn.disabled = count === 0;
      }
    });
  });

  // Handle booking form submission via AJAX
  if (bookBtn) {
    bookBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      if (selectedSeats.length === 0) return;

      const movieId = seatGrid.dataset.movieId;
      const location = seatGrid.dataset.location;

      bookBtn.disabled = true;
      bookBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Processing Booking...';

      try {
        const response = await fetch('/api/book-seats', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            movie_id: movieId,
            seats: selectedSeats,
            location: location,
            booking_date: new Date().toISOString().split('T')[0]
          })
        });

        const data = await response.json();

        if (data.success) {
          showSNSToast(
            `🎬 Booking Confirmed! [ID: ${data.booking_id}]`,
            `Instant notification payload sent via AWS SNS to your email!`
          );
          setTimeout(() => {
            window.location.href = data.redirect_url;
          }, 1500);
        } else {
          alert(`Booking Failed: ${data.message}`);
          bookBtn.disabled = false;
          bookBtn.innerHTML = '⚡ Confirm & Pay Now';
        }
      } catch (err) {
        console.error('Booking error:', err);
        alert('Server connection error. Please try again.');
        bookBtn.disabled = false;
        bookBtn.innerHTML = '⚡ Confirm & Pay Now';
      }
    });
  }
}

// ------------------ AWS SNS TOAST NOTIFICATION ------------------
function showSNSToast(title, body) {
  const toast = document.createElement('div');
  toast.className = 'sns-toast';
  toast.innerHTML = `
    <div class="d-flex align-items-center justify-content-between mb-2">
      <span class="aws-pill">AWS SNS Notification</span>
      <button type="button" class="btn-close btn-close-white btn-sm" onclick="this.parentElement.parentElement.remove()"></button>
    </div>
    <h6 class="fw-bold mb-1 text-white">${title}</h6>
    <p class="small text-muted mb-0">${body}</p>
  `;
  document.body.appendChild(toast);

  setTimeout(() => {
    if (document.body.contains(toast)) {
      toast.remove();
    }
  }, 7000);
}

// ------------------ ALERTS AUTO DISMISS ------------------
function initAutoDismissAlerts() {
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(alert => {
    setTimeout(() => {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });
}

// ------------------ FETCH USER NOTIFICATIONS ------------------
async function checkUserNotifications() {
  try {
    const res = await fetch('/api/user-notifications');
    if (res.ok) {
      const notifs = await res.json();
      if (notifs && notifs.length > 0) {
        console.log(`[MovieMagic] Loaded ${notifs.length} notifications.`);
      }
    }
  } catch (e) {
    // Ignore silent errors
  }
}
