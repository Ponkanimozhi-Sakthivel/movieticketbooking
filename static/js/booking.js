document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('booking-form');
    const checkboxes = document.querySelectorAll('input[name="seats[]"]');
    const selectedSeatsSpan = document.getElementById('selected-seats');
    const totalAmountSpan = document.getElementById('total-amount');
    const bookBtn = document.getElementById('book-btn');
    
    const PRICE_PER_TICKET = parseFloat(document.querySelector('.price-summary').getAttribute('data-price'));

    function updateSummary() {
        const selectedSeats = Array.from(checkboxes).filter(cb => cb.checked);
        const seatCount = selectedSeats.length;
        const totalAmount = seatCount * PRICE_PER_TICKET;

        selectedSeatsSpan.textContent = seatCount;
        totalAmountSpan.textContent = totalAmount.toFixed(2);
        
        bookBtn.disabled = seatCount === 0;
        bookBtn.classList.toggle('btn-active', seatCount > 0);

        // Update seat visuals
        checkboxes.forEach(checkbox => {
            const label = document.querySelector(`label[for="${checkbox.id}"]`);
            if (label) {
                label.classList.toggle('selected', checkbox.checked);
            }
        });
    }

    // Handle seat clicks
    document.querySelectorAll('.seat:not(.booked)').forEach(seat => {
        seat.addEventListener('click', function(e) {
            e.preventDefault();
            const checkbox = document.getElementById(this.getAttribute('for'));
            if (checkbox && !checkbox.disabled) {
                checkbox.checked = !checkbox.checked;
                this.classList.toggle('selected', checkbox.checked);
                updateSummary();
            }
        });
    });

    // Handle form submission with retries
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const selectedSeats = Array.from(checkboxes).filter(cb => cb.checked);
        if (selectedSeats.length === 0) {
            alert('Please select at least one seat');
            return;
        }

        const seatNumbers = selectedSeats.map(cb => cb.value).join(', ');
        const totalAmount = selectedSeats.length * PRICE_PER_TICKET;

        if (confirm(`Confirm booking for:\nSeats: ${seatNumbers}\nTotal amount: ₹${totalAmount.toFixed(2)}`)) {
            try {
                bookBtn.disabled = true;
                bookBtn.textContent = 'Processing...';
                
                const formData = new FormData(form);
                const response = await fetch(window.location.href, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const data = await response.json();
                
                if (data.success) {
                    window.location.href = data.redirect;
                } else {
                    alert(data.message || 'Booking failed. Please try again.');
                    window.location.reload();
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Network error. Please try again.');
                window.location.reload();
            } finally {
                bookBtn.disabled = false;
                bookBtn.textContent = 'Confirm Booking';
            }
        }
    });

    // Initialize
    updateSummary();
});