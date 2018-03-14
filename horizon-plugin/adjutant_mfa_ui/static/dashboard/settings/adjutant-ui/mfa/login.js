function togglePasscodeField(){
  var checked = document.getElementById('id_mfa_enabled_toggle').checked;
  if (checked){
    document.getElementById('id_passcode_div').hidden = false;
  }else{
    document.getElementById('id_passcode_div').hidden = true;
  }
}

function processLoginWithPasscode(e) {
  console.log("here")
  var checked = document.getElementById('id_mfa_enabled_toggle').checked;
  if (checked) {
    // Append the TOTP passcode to the password
    var totpPasscode = document.getElementById('id_passcode').value;
    document.getElementById('id_password').value += totpPasscode;
  }

}

id_mfa_enabled_toggle = document.getElementById('id_mfa_enabled_toggle');
if (id_mfa_enabled_toggle !== null){
  id_mfa_enabled_toggle.addEventListener('click', togglePasscodeField);

  // Since the above div isn't null, we must be on the login page
  var form = document.forms[0]; // Form ID is not set, this functions on the
                                // assumption that there is not multiple forms
  if (form.attachEvent) {
      form.attachEvent("submit", processLoginWithPasscode);
  } else {
      form.addEventListener("submit", processLoginWithPasscode);
  }

}
