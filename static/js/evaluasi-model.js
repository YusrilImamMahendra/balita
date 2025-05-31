// Fungsi untuk memformat angka dengan 2 desimal dan menambahkan %
function formatPercentage(value) {
    return value.toFixed(2) + '%';
}

// Fungsi untuk memperbarui confusion matrix
function updateConfusionMatrix(matrix) {
    const cells = document.querySelectorAll('.confusion-matrix tbody td');
    matrix.forEach((row, i) => {
        row.forEach((value, j) => {
            const index = (i * 3) + j;
            cells[index].textContent = value;
            cells[index].className = i === j ? 'table-success' : 'table-danger';
        });
    });
}

// Fungsi untuk memperbarui metrik per kelas
function updateClassMetrics(evaluation) {
    const statuses = ['Normal', 'Kurang', 'Buruk'];
    statuses.forEach((status, i) => {
        document.querySelector(`#sensitivity-${status.toLowerCase()}`).textContent = 
            formatPercentage(evaluation.sensitivitas_per_kelas[i] * 100);
        document.querySelector(`#specificity-${status.toLowerCase()}`).textContent = 
            formatPercentage(evaluation.spesifisitas_per_kelas[i] * 100);
        document.querySelector(`#f1-${status.toLowerCase()}`).textContent = 
            formatPercentage(evaluation.f1_per_kelas[i] * 100);
    });
}

// Fungsi utama untuk memperbarui data evaluasi
function updateEvaluation() {
    fetch('/evaluasi_model/data')
        .then(response => response.json())
        .then(data => {
            if (data.model_evaluation) {
                // Update metrik utama
                document.querySelector('.accuracy-value').textContent =                     
                    data.model_evaluation.accuracy.toFixed(2) + '%';
                document.querySelector('.cv-mean-value').textContent = 
                    formatPercentage(data.model_evaluation.cv_mean);
                document.querySelector('.cv-std-value').textContent = 
                    '± ' + formatPercentage(data.model_evaluation.cv_std);

                // Update confusion matrix
                updateConfusionMatrix(data.model_evaluation.confusion_matrix);

                // Update metrik per kelas
                updateClassMetrics(data.model_evaluation);

                // Update waktu terakhir update
                document.querySelector('.last-updated').textContent = 
                    'Terakhir diperbarui: ' + data.last_updated;

                // Tampilkan notifikasi sukses
                const toast = document.createElement('div');
                toast.className = 'toast-success';
                toast.textContent = 'Data evaluasi berhasil diperbarui';
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 3000);
            }
        })
        .catch(error => {
            console.error('Error updating evaluation:', error);
            // Tampilkan notifikasi error
            const toast = document.createElement('div');
            toast.className = 'toast-error';
            toast.textContent = 'Gagal memperbarui data evaluasi';
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        });
}

// CSS untuk notifikasi toast
const style = document.createElement('style');
style.textContent = `
.toast-success, .toast-error {
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 10px 20px;
    border-radius: 4px;
    color: white;
    animation: fadeIn 0.3s, fadeOut 0.3s 2.7s;
    z-index: 1000;
}

.toast-success {
    background-color: #28a745;
}

.toast-error {
    background-color: #dc3545;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeOut {
    from { opacity: 1; transform: translateY(0); }
    to { opacity: 0; transform: translateY(20px); }
}
`;
document.head.appendChild(style);

// Jalankan update pertama kali saat halaman dimuat
document.addEventListener('DOMContentLoaded', () => {
    updateEvaluation();
    // Set interval untuk update otomatis setiap 30 detik
    setInterval(updateEvaluation, 30000);
});