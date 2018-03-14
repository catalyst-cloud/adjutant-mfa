qr_div = document.getElementById("mfa-qrcode");

if (qr_div !== null){
  if (typeof QRCode !== 'undefined') {
    new QRCode(qr_div, {
      text: qr_div.getAttribute("data-provisioning-url"),
      width: 200,
      height: 200,
      correctLevel : QRCode.CorrectLevel.H
    });
  } else {
    addHorizonLoadEvent(function() {
      new QRCode(qr_div, {
        text: qr_div.getAttribute("data-provisioning-url"),
        width: 200,
        height: 200,
        correctLevel : QRCode.CorrectLevel.H
      });
    });
  }
}

function toggleAdditionalDetails(){
  var additional_details = document.getElementById("id_additional_totp_details");
  if (additional_details.hidden){
    additional_details.hidden = false;
  } else {
    additional_details.hidden = true;
  }
}

totp_details_toggle = document.getElementById('id_additional_details_toggle');

if (totp_details_toggle !== null){
  totp_details_toggle.addEventListener('click', toggleAdditionalDetails);
}
