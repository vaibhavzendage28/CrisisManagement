var show = document.getElementById("show");
var opn = document.getElementById("open");
opn.addEventListener("click", function () {
show.classList.toggle("active");
});

document.querySelectorAll(".accordion-item").forEach((item) => {
item.querySelector(".accordion-item-header").addEventListener("click", () => {
item.classList.toggle("open");
});
});
      