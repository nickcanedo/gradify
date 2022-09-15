const github = document.querySelector(".fa-github");

github.addEventListener("mouseenter", () => {
    github.classList.add("fa-bounce");
});

github.addEventListener("mouseleave", () => {
    github.classList.remove("fa-bounce");
});