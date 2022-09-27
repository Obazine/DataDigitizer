const particles = [];

function windowResized() {
    resizeCanvas(windowWidth, windowHeight);
}

function setup() {
    createCanvas(window.outerWidth, window.outerHeight);

    const particlesLength = Math.floor(window.innerWidth / 10);

    for(let i = 0; i < particlesLength; i++) {
        particles.push(new Particle());
    }
}

function draw() {
    background(47,48,56);
    particles.forEach((p, index) => {
        p.update();
        p.draw();
        p.checkParticles(particles.slice(index));
    })
}

class Particle {
    constructor() {
        // position
        this.pos = createVector(random(width), random(height));
        // velocity
        this.vel = createVector(random(-2, 2), random(-2, 2));
        // size
        this.size = 10;
    }

    update() {
        this.pos.add(this.vel);
        this.edges();
    }

    draw() {
        noStroke();
        fill('rgba(255,255,255,0.5)');
        circle(this.pos.x, this.pos.y, this.size);
    }


    edges() {
        if(this.pos.x < 0 || this.pos.x > width) {
            this.vel.x *= -1;
        }
        if(this.pos.y < 0 || this.pos.y > height) {
            this.vel.y *= -1;
        }
    }

    checkParticles(particles) {
        particles.forEach(particle => {
            const d = dist(this.pos.x, this.pos.y, particle.pos.x, particle.pos.y)

            if(d < 120) {
                stroke('rgba(255,255,255,0.1)');
                line(this.pos.x, this.pos.y, particle.pos.x, particle.pos.y)
            }
        });
    }
}

const realFileBtn = document.getElementById("image-input");
const image_input = document.querySelector("#image-input");
var uploaded_image = "";
function LoadNewImage() {
    realFileBtn.click();
}

image_input.addEventListener("change", function() {
    const reader = new FileReader();
    reader.addEventListener("load", () => {
        const base64String = reader.result.replace('data:', '').replace(/^.+,/, '');
        localStorage.setItem('wallpaper', base64String);
    });
    reader.readAsDataURL(this.files[0]);
    var dataImage = localStorage.getItem('wallpaper');
    bannerImg = document.getElementById('actual-image');
    bannerImg.src = "data:image/png;base64," +dataImage
})