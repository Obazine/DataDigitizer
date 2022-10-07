//particle background creation
const particles = [];
function windowResized() {
    resizeCanvas(windowWidth, windowHeight);
}

function setup() {
    createCanvas(window.outerWidth, window.outerHeight);
    canvas.id = "particles"
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
        this.pos = createVector(random(width), random(height));
        this.vel = createVector(random(-2, 2), random(-2, 2));
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


//image processing
const realFileBtn = document.getElementById("image-input");
function LoadNewImage() {
    realFileBtn.click();
}

var img = document.getElementById("graph-image")
var preview = document.querySelector(".zoom-preview");
  
        //calculating the ratio by which we want to magnify the image
        //you can increase or decrease it according to your requirement
        var x = preview.offsetWidth / 100;
        var y = preview.offsetHeight / 100;
  
        img.addEventListener("mousemove", (e) => {
            preview.style.backgroundImage = `url(${img.src})`;
            preview.style.backgroundSize = img.width * x + 
              "px " + img.height * y + "px";
            var posX = e.offsetX - 50;
            var posY = e.offsetY - 50;
            preview.style.backgroundPosition = "-" + posX * x + 
              "px -" + posY * y + "px";
        });
        img.addEventListener("mouseout", () => {
            preview.style.backgroundImage = "none";
        });