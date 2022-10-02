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
function LoadNewImage() {
    realFileBtn.click();
}

let imgElement = document.getElementById('actual-image');
let inputElement = document.getElementById('image-input');
inputElement.addEventListener('change', (e) => {
    imgElement.src = URL.createObjectURL(e.target.files[0]);
}, false);
imgElement.onload = function () {
    let mat = cv.imread(imgElement);
    cv.cvtColor(mat, mat, cv.COLOR_RGB2GRAY, 0);
    cv.Canny(mat, mat, 50, 100, 3, false);
    cv.imshow('canvasOutput', mat);
    mat.delete();
};
