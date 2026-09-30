/**
 * SOFTWARE MANAGEMENT SYSTEM - CLIENT SCRIPT
 * Handles Modals, Form Pre-filling, Delete Confirmations, and Alerts
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Auto-dismiss Flash Alerts after 5 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function () {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 250);
      });
    }
    setTimeout(function () {
      if (document.body.contains(alert)) {
        alert.style.transition = 'opacity 0.4s ease';
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 400);
      }
    }, 6000);
  });

  // 2. Close Modal on ESC key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      closeAllModals();
    }
  });

  // 3. Close Modal on clicking backdrop
  document.querySelectorAll('.modal-overlay').forEach(function (modal) {
    modal.addEventListener('click', function (e) {
      if (e.target === modal) {
        modal.classList.remove('active');
      }
    });
  });
});

/**
 * Open Modal by Element ID
 */
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.add('active');
    // Auto-focus first input if present
    const firstInput = modal.querySelector('input:not([type=hidden]), select, textarea');
    if (firstInput) {
      setTimeout(() => firstInput.focus(), 100);
    }
  }
}

/**
 * Close Modal by Element ID
 */
function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.remove('active');
  }
}

/**
 * Close all active modals
 */
function closeAllModals() {
  document.querySelectorAll('.modal-overlay.active').forEach(function (modal) {
    modal.classList.remove('active');
  });
}

/**
 * Confirm deletion dialog
 */
function confirmDelete(entityName, itemName) {
  const message = itemName 
    ? `Are you sure you want to delete ${entityName}: "${itemName}"?\nThis action cannot be undone.`
    : `Are you sure you want to delete this ${entityName}?`;
  return confirm(message);
}

// -----------------------------------------------------------------------------
// Pre-fill Edit Modal Handlers for each Entity
// -----------------------------------------------------------------------------

function populateEditUser(id, name, email) {
  const form = document.getElementById('editUserForm');
  if (form) {
    form.action = `/users/edit/${id}`;
    document.getElementById('edit_user_name').value = name;
    document.getElementById('edit_user_email').value = email;
    document.getElementById('edit_user_password').value = '';
    openModal('editUserModal');
  }
}

function populateEditDepartment(id, name, desc, location, email) {
  const form = document.getElementById('editDeptForm');
  if (form) {
    form.action = `/departments/edit/${id}`;
    document.getElementById('edit_dept_name').value = name;
    document.getElementById('edit_dept_desc').value = desc || '';
    document.getElementById('edit_dept_location').value = location || '';
    document.getElementById('edit_dept_email').value = email || '';
    openModal('editDeptModal');
  }
}

function populateEditProject(id, name, desc, start, end, status, deptId) {
  const form = document.getElementById('editProjectForm');
  if (form) {
    form.action = `/projects/edit/${id}`;
    document.getElementById('edit_project_name').value = name;
    document.getElementById('edit_project_desc').value = desc || '';
    document.getElementById('edit_project_start').value = start || '';
    document.getElementById('edit_project_end').value = end || '';
    document.getElementById('edit_project_status').value = status;
    document.getElementById('edit_project_dept').value = deptId;
    openModal('editProjectModal');
  }
}

function populateEditDeveloper(id, name, email, deptId) {
  const form = document.getElementById('editDeveloperForm');
  if (form) {
    form.action = `/developers/edit/${id}`;
    document.getElementById('edit_dev_name').value = name;
    document.getElementById('edit_dev_email').value = email;
    document.getElementById('edit_dev_dept').value = deptId;
    openModal('editDeveloperModal');
  }
}

function populateEditSoftware(id, name, desc, status, projectId, techIdsJson) {
  const form = document.getElementById('editSoftwareForm');
  if (form) {
    form.action = `/software/edit/${id}`;
    document.getElementById('edit_software_name').value = name;
    document.getElementById('edit_software_desc').value = desc || '';
    document.getElementById('edit_software_status').value = status;
    document.getElementById('edit_software_project').value = projectId;

    // Reset and check technologies checkboxes
    let techIds = [];
    try {
      techIds = JSON.parse(techIdsJson || '[]');
    } catch (e) {
      techIds = [];
    }

    const checkboxes = form.querySelectorAll('input[name="technologies"]');
    checkboxes.forEach(function (cb) {
      cb.checked = techIds.includes(parseInt(cb.value));
    });

    openModal('editSoftwareModal');
  }
}

function populateEditVersion(id, softwareId, versionNumber, releaseDate) {
  const form = document.getElementById('editVersionForm');
  if (form) {
    form.action = `/versions/edit/${id}`;
    document.getElementById('edit_version_software').value = softwareId;
    document.getElementById('edit_version_number').value = versionNumber;
    document.getElementById('edit_version_release').value = releaseDate;
    openModal('editVersionModal');
  }
}

function populateEditBug(id, softwareId, desc, severity, status, reportedDate) {
  const form = document.getElementById('editBugForm');
  if (form) {
    form.action = `/bugs/edit/${id}`;
    document.getElementById('edit_bug_software').value = softwareId;
    document.getElementById('edit_bug_desc').value = desc;
    document.getElementById('edit_bug_severity').value = severity;
    document.getElementById('edit_bug_status').value = status;
    document.getElementById('edit_bug_date').value = reportedDate;
    openModal('editBugModal');
  }
}

function populateEditMaintenance(id, bugId, maintDate, desc, performedBy, status) {
  const form = document.getElementById('editMaintenanceForm');
  if (form) {
    form.action = `/maintenance/edit/${id}`;
    document.getElementById('edit_maint_bug').value = bugId;
    document.getElementById('edit_maint_date').value = maintDate;
    document.getElementById('edit_maint_desc').value = desc;
    document.getElementById('edit_maint_performed').value = performedBy;
    document.getElementById('edit_maint_status').value = status;
    openModal('editMaintenanceModal');
  }
}

function populateEditLicense(id, softwareId, type, start, expiry, status) {
  const form = document.getElementById('editLicenseForm');
  if (form) {
    form.action = `/licenses/edit/${id}`;
    document.getElementById('edit_license_software').value = softwareId;
    document.getElementById('edit_license_type').value = type;
    document.getElementById('edit_license_start').value = start;
    document.getElementById('edit_license_expiry').value = expiry;
    document.getElementById('edit_license_status').value = status;
    openModal('editLicenseModal');
  }
}

function populateEditTechnology(id, name, type, version, desc) {
  const form = document.getElementById('editTechnologyForm');
  if (form) {
    form.action = `/technologies/edit/${id}`;
    document.getElementById('edit_tech_name').value = name;
    document.getElementById('edit_tech_type').value = type;
    document.getElementById('edit_tech_version').value = version || '';
    document.getElementById('edit_tech_desc').value = desc || '';
    openModal('editTechnologyModal');
  }
}
