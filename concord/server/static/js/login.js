function postToken() {
    var xhr = new XMLHttpRequest();
    var url = "/api/login";
    var data = "token=" + document.getElementById("token").value +
        "&server_name=" + document.getElementById("server_name").value;
    xhr.open("POST", url, true);
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded;charset=UTF-8");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 201) {
            const jsonResponse = JSON.parse(xhr.responseText);
            setTimeout(document.location = jsonResponse.graphURL, 4000);
        }
    };
    xhr.send(data);
    return false;
}