// Trying to make this work for anything ES6 compliant
// Author: Kieran Gee
// License: MIT
// Works on:
//   - IE 8
//   - Firefox 142
//   - Safari 26
//   - Firefox 4
// Does not work on:
//   - IE 6
//   - IE 7
//   - Firefox 3

// Root object for file system structure
var file_structure = {};

// IE6 Help
if (! console) {
  console = {};
  console.log = function (msg) {alert(msg);};
}

// Show the JS generated divs and hide the original file list
function showJSDivs() {
  var breadcrumbJSDiv = document.getElementById("breadcrumb_js");
  if (breadcrumbJSDiv) {
    breadcrumbJSDiv.style.display = "block";
  }
  var fileListJSDiv = document.getElementById("file_list_js");
  if (fileListJSDiv) {
    fileListJSDiv.style.display = "block";
  }
}

// Add a file to the file structure object
function addFileToStructure(url, file_path) {
  var path_parts = file_path.split("/");
  var current = file_structure;
  var i;
  for (i = 0; i < path_parts.length; i++) {
    if (!current[path_parts[i]]) {
      current[path_parts[i]] = {};
    }
    current = current[path_parts[i]];
  }
  current.url = url;
}

// Generate breadcrumb HTML
function generateBreadcrumbHtml(in_current_path) {
  var html = "";
  var path = [""];
  var i, current;

  if (in_current_path !== "/") {
    path = in_current_path.split("/");
  }
  path.shift();

  current = "";
  html += '<a href="#/">File list</a> / ';
  for (i = 0; i < path.length; i++) {
    current = current + "/" + path[i];
    current = current.replace(/\/\//g, "/");
    html += '<a href="#' + current + '/">' + path[i] + "</a> / ";
  }
  return html;
}

// Generate current directory listing HTML
function generateCurrentListHTML(in_current_path, items) {
  var html = "";
  var current_path_nice = in_current_path;
  var current_path_split;
  var key, value;

  if (in_current_path !== "/") {
    current_path_split = current_path_nice.split("/");
    current_path_split.pop();
    current_path_split = current_path_split.join("/");
    html += '<li>📂 <a href="#' + current_path_split + '/">..</a></li>';
  } else {
    current_path_nice = "";
  }

  if (items && typeof items === "object") {
    for (key in items) {
      if (items.hasOwnProperty(key)) {
        value = items[key];
        if (value.url === undefined) {
          html += '<li>📂 <a href="#' + current_path_nice + "/" + key + '/" ;>' + key + "/</a></li>";
        }
      }
    }

    for (key in items) {
      if (items.hasOwnProperty(key)) {
        value = items[key];
        if (value.url !== undefined) {
          html += '<li>💾 <a href="' + value.url + '">' + key + "</a></li>";
        }
      }
    }
  }

  html += "";
  return html;
}

// Retrieve value from nested object based on path
function getValue(obj, path) {
  var keys, current, i;
  if (path === "/") return obj[""];
  keys = path.split("/"); // Split the path by '/' into an array of keys.
  current = obj;
  for (i = 0; i < keys.length; i++) {
    if (current && current[keys[i]] !== undefined) {
      current = current[keys[i]];
    } else {
      return undefined;
    }
  }
  return current;
}

function checkValidPath(path) {
  var path_parts, current, i;
  if (path === "" || path === "/") {
    return true;
  }
  path_parts = path.split("/");
  current = file_structure;
  for (i = 0; i < path_parts.length; i++) {
    if (!current[path_parts[i]]) {
      console.log("Invalid path: ", path);
      return false;
    }
    current = current[path_parts[i]];
  }
  return true;
}

// Get the current path from the URL hash
function getNicePathStr() {
  var path = window.location.hash;
  path = path.replace("#", ""); // Remove the hash
  path = decodeURIComponent(path); // Decode URL-encoded characters (e.g., spaces)

  if (path === "" || path === "/") {
    // If the path is empty or just a slash, return a single slash
    return "/";
  }
  path = path.replace(/\/+/g, "/"); // Replace double slashes with a single slash
  if (path[path.length - 1] === "/") {
    // Remove trailing slash
    path = path.slice(0, -1);
  }
  return path;
}

// Show the current directory based on the URL hash
function showCurrentDirectory() {
  var current_path = getNicePathStr();
  var breadcrumbJSDiv, fileListJSDiv, items;

  // Handle invalid paths
  if (!checkValidPath(current_path)) {
    breadcrumbJSDiv = document.getElementById("breadcrumb_js");
    breadcrumbJSDiv.innerHTML = generateBreadcrumbHtml("/");
    fileListJSDiv = document.getElementById("file_list_js");
    fileListJSDiv.innerHTML = "<li>Invalid path: " + current_path + "</li>";
    return;
  }

  // Normalize the current path
  current_path = current_path.replace(/\/\//g, "/");
  if (current_path[current_path.length - 1] === "/") {
    current_path = current_path.slice(0, -1);
  }
  if (current_path === "") {
    current_path = "/";
  }

  // Update breadcrumb
  breadcrumbJSDiv = document.getElementById("breadcrumb_js");
  if (breadcrumbJSDiv) {
    breadcrumbJSDiv.innerHTML = generateBreadcrumbHtml(current_path);
  }

  //File List
  items = getValue(file_structure, current_path);
  fileListJSDiv = document.getElementById("file_list_js");
  if (fileListJSDiv) {
    fileListJSDiv.innerHTML = generateCurrentListHTML(current_path, items);
  }
}

// Initialize file list
function initFileList() {
  var fileListDiv = document.getElementById("file_list");
  var links, link, i;
  if (fileListDiv) {
    fileListDiv.style.display = "none";
    links = fileListDiv.getElementsByTagName("a");
    for (i = 0; i < links.length; i++) {
      link = links[i];
      if (link && link.firstChild) {
        addFileToStructure(
          link.href,
          link.firstChild.nodeValue || link.firstChild.textContent || link.firstChild.innerText
        );
      }
    }
  }
  showJSDivs();
  showCurrentDirectory();
}

// Handle navigation
initFileList();

if (window.addEventListener) {
  console.log("Using addEventListener, modern browser");
  window.addEventListener("hashchange", showCurrentDirectory, false);
  showCurrentDirectory();
} else if (window.attachEvent) {
  // Hopefully gives us IE8? support
  console.log("Using attachEvent, old IE");
  window.attachEvent("onhashchange", showCurrentDirectory);
  showCurrentDirectory();
}
