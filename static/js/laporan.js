function updateConfusionMatrix(matrix, classNames) {
    const tbody = document.querySelector('.confusion-matrix tbody');
    matrix.forEach((row, i) => {
        row.forEach((value, j) => {
            const cell = tbody.rows[i].cells[j + 2]; // +2 karena ada 2 kolom header
            cell.textContent = value;
            cell.className = i === j ? 'table-success' : 'table-danger';
        });
    });
}

function updateClassMetrics(evaluation) {
    evaluation.class_names.forEach((className, i) => {
        const lowerClassName = className.toLowerCase();
        document.querySelector(`#sensitivity-${lowerClassName}`).textContent = 
            formatPercentage(evaluation.sensitivitas_per_kelas[i] * 100);
        document.querySelector(`#specificity-${lowerClassName}`).textContent = 
            formatPercentage(evaluation.spesifisitas_per_kelas[i] * 100);
        document.querySelector(`#precision-${lowerClassName}`).textContent = 
            formatPercentage(evaluation.presisi_per_kelas[i] * 100);
        document.querySelector(`#f1-${lowerClassName}`).textContent = 
            formatPercentage(evaluation.f1_per_kelas[i] * 100);
    });
}

// Update fungsi utama
function updateEvaluation() {
    fetch('/evaluasi_model/data')
        .then(response => response.json())
        .then(data => {
            if (data.model_evaluation) {
                // Update metrik utama
                document.querySelector('.accuracy-value').textContent = 
                    formatPercentage(data.model_evaluation.accuracy);
                document.querySelector('.cv-mean-value').textContent = 
                    formatPercentage(data.model_evaluation.cv_mean);
                document.querySelector('.cv-std-value').textContent = 
                    '± ' + formatPercentage(data.model_evaluation.cv_std);

                // Update confusion matrix dan metrik per kelas
                updateConfusionMatrix(
                    data.model_evaluation.confusion_matrix,
                    data.model_evaluation.class_names
                );
                updateClassMetrics(data.model_evaluation);

                // Update waktu terakhir
                document.querySelector('.last-updated').textContent = 
                    'Terakhir diperbarui: ' + data.last_updated;

                showToast('success', 'Data evaluasi berhasil diperbarui');
            }
        })
        .catch(error => {
            console.error('Error updating evaluation:', error);
            showToast('error', 'Gagal memperbarui data evaluasi');
        });
}