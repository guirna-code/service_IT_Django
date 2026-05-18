document.addEventListener('DOMContentLoaded', function () {
  var sidebarCanvas = document.getElementById('sidebarCanvas');
  if (!sidebarCanvas) {
    return;
  }

  sidebarCanvas.querySelectorAll('.sidebar-link').forEach(function (link) {
    link.addEventListener('click', function () {
      var offcanvas = bootstrap.Offcanvas.getInstance(sidebarCanvas);
      if (offcanvas) {
        offcanvas.hide();
      }
    });
  });
});
