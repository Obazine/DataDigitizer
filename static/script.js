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

//Magnifier Glass
var mainImg = document.getElementById("graph-image");
var preview = document.querySelector(".zoom-preview");

var x = preview.offsetWidth / 100;
var y = preview.offsetHeight / 100;

mainImg.addEventListener("mousemove", (e) => {
    preview.style.backgroundImage = `url(${mainImg.src})`;
    preview.style.backgroundSize = mainImg.width * x + 
      "px " + mainImg.height * y + "px";
    var posX = e.offsetX - 50;
    var posY = e.offsetY - 50;
    preview.style.backgroundPosition = "-" + posX * x + 
        "px -" + posY * y + "px";
});
mainImg.addEventListener("mouseout", () => {
    preview.style.backgroundImage = "none";
});


//Axes Callibration
callibrateAxesActivated = false;
axesCoords = []
function callibrateAxes(){
    callibrateAxesActivated = true;
};
function recordCoords(event) {
    if(axesCoords.length < 4 && callibrateAxesActivated)
    {
        var x = event.clientX;
        var y = event.clientY;  
        tempCoord = [x, y]
        axesCoords.push(tempCoord)
        var coords = "X coords: " + x + ", Y coords: " + y;
        console.log(coords);
    };
};