// ფილტრი მოთხოვნების სტატუსის მიხედვით
document.getElementById('statusFilter')?.addEventListener('change', function () {
  const selected = this.value;
  document.querySelectorAll('tbody tr').forEach(tr => {
    const status = tr.getAttribute('data-status');
    tr.style.display = (!selected || selected === status) ? '' : 'none';
  });
});
