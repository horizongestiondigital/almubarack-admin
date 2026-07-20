// Construit les cartes produits, gère filtres, recherche, galerie multi-images,
// section Nouveautés, zoom (lightbox) et bouton retour en haut.
const NUMERO_WHATSAPP = "224625476147";
const NB_NOUVEAUTES = 4;

let categorieActive = "tous";
let termeRecherche = "";

function creerMessageWhatsapp(nomProduit) {
    const texte = `Bonjour, je suis intéressé(e) par : ${nomProduit}. Est-il disponible ?`;
    return `https://wa.me/${NUMERO_WHATSAPP}?text=${encodeURIComponent(texte)}`;
}

function imagesDuProduit(produit) {
    if (Array.isArray(produit.images) && produit.images.length > 0) return produit.images;
    if (produit.image) return [produit.image];
    return [];
}

function ouvrirLightbox(src, alt) {
    const lightbox = document.getElementById("lightbox");
    const img = document.getElementById("lightbox-image");
    img.src = src;
    img.alt = alt;
    lightbox.classList.add("ouvert");
    document.body.style.overflow = "hidden";
}

function fermerLightbox() {
    document.getElementById("lightbox").classList.remove("ouvert");
    document.body.style.overflow = "";
}

function ouvrirModalDetails(produit, imageActuelle) {
    document.getElementById("modal-details-image").src = imageActuelle;
    document.getElementById("modal-details-image").alt = produit.nom;
    document.getElementById("modal-details-titre").textContent = produit.nom;

    const listeSpecs = document.getElementById("modal-details-specs");
    listeSpecs.innerHTML = "";
    const specs = produit.details && produit.details.length > 0
        ? produit.details
        : ["Aucune information supplémentaire — contacte-nous sur WhatsApp pour plus de détails."];
    specs.forEach(ligne => {
        const li = document.createElement("li");
        li.textContent = ligne;
        listeSpecs.appendChild(li);
    });

    document.getElementById("modal-details-whatsapp").href = creerMessageWhatsapp(produit.nom);
    document.getElementById("modal-details").classList.add("ouvert");
    document.body.style.overflow = "hidden";
}

function fermerModalDetails() {
    document.getElementById("modal-details").classList.remove("ouvert");
    document.body.style.overflow = "";
}

function creerCarteProduit(produit) {
    const carte = document.createElement("article");
    carte.className = "carte-produit";
    carte.dataset.categorie = produit.categorie;

    const badge = produit.badge || "Disponible";
    const images = imagesDuProduit(produit);
    const plusieursImages = images.length > 1;

    const pointsHtml = plusieursImages
        ? `<div class="galerie-points">${images.map((_, i) => `<span class="point ${i === 0 ? 'actif' : ''}" data-index="${i}"></span>`).join("")}</div>`
        : "";
    const flechesHtml = plusieursImages
        ? `<button class="galerie-fleche galerie-fleche-gauche" aria-label="Image précédente">‹</button>
           <button class="galerie-fleche galerie-fleche-droite" aria-label="Image suivante">›</button>`
        : "";

    carte.innerHTML = `
        <div class="carte-image-wrap">
            <span class="carte-badge">${badge}</span>
            <img src="${images[0] || ''}" alt="${produit.nom}" loading="lazy" class="carte-image" data-index-actuel="0">
            <span class="icone-zoom">🔍</span>
            ${flechesHtml}
            ${pointsHtml}
        </div>
        <div class="carte-contenu">
            <h3>${produit.nom}</h3>
            <button type="button" class="btn-details">📋 Voir les détails</button>
            <a href="${creerMessageWhatsapp(produit.nom)}" target="_blank" class="btn-commander">
                <span class="icone-whatsapp">●</span> Commander sur WhatsApp
            </a>
        </div>
    `;

    const imgEl = carte.querySelector(".carte-image");

    imgEl.addEventListener("click", () => {
        ouvrirLightbox(imgEl.src, produit.nom);
    });

    carte.querySelector(".btn-details").addEventListener("click", () => {
        ouvrirModalDetails(produit, imgEl.src);
    });

    if (plusieursImages) {
        const points = carte.querySelectorAll(".point");

        function afficherImage(index) {
            imgEl.src = images[index];
            imgEl.dataset.indexActuel = index;
            points.forEach(p => p.classList.remove("actif"));
            points[index].classList.add("actif");
        }

        points.forEach(point => {
            point.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                afficherImage(parseInt(point.dataset.index, 10));
            });
        });

        carte.querySelector(".galerie-fleche-gauche").addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            const actuel = parseInt(imgEl.dataset.indexActuel, 10);
            afficherImage((actuel - 1 + images.length) % images.length);
        });
        carte.querySelector(".galerie-fleche-droite").addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            const actuel = parseInt(imgEl.dataset.indexActuel, 10);
            afficherImage((actuel + 1) % images.length);
        });
    }

    return carte;
}

function produitsFiltres() {
    return PRODUITS.filter(p => {
        const matchCategorie = categorieActive === "tous" || p.categorie === categorieActive;
        const matchRecherche = termeRecherche === "" || p.nom.toLowerCase().includes(termeRecherche);
        return matchCategorie && matchRecherche;
    });
}

function rafraichirCatalogue() {
    const catalogue = document.getElementById("catalogue");
    catalogue.innerHTML = "";

    const produits = produitsFiltres();

    if (produits.length === 0) {
        catalogue.innerHTML = '<p class="catalogue-vide">Aucun produit ne correspond à ta recherche.</p>';
        return;
    }

    produits.forEach((produit, index) => {
        const carte = creerCarteProduit(produit);
        carte.style.animationDelay = `${Math.min(index * 0.04, 0.4)}s`;
        catalogue.appendChild(carte);
    });
}

function afficherNouveautes() {
    const grille = document.getElementById("nouveautes-grille");
    if (!grille) return;

    // Les "derniers ajoutés" = les N derniers éléments du tableau PRODUITS
    const derniers = PRODUITS.slice(-NB_NOUVEAUTES).reverse();

    derniers.forEach((produit, index) => {
        const carte = creerCarteProduit(produit);
        carte.style.animationDelay = `${index * 0.05}s`;
        grille.appendChild(carte);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    afficherNouveautes();
    rafraichirCatalogue();

    document.querySelectorAll(".filtre-btn").forEach(bouton => {
        bouton.addEventListener("click", () => {
            document.querySelectorAll(".filtre-btn").forEach(b => b.classList.remove("actif"));
            bouton.classList.add("actif");
            categorieActive = bouton.dataset.cat;
            rafraichirCatalogue();
            document.getElementById("filtres").scrollIntoView({ behavior: "smooth", block: "start" });
        });
    });

    const champRecherche = document.getElementById("recherche");
    champRecherche.addEventListener("input", (e) => {
        termeRecherche = e.target.value.trim().toLowerCase();
        rafraichirCatalogue();
    });

    // Lightbox
    document.querySelector(".lightbox-fermer").addEventListener("click", fermerLightbox);
    document.getElementById("lightbox").addEventListener("click", (e) => {
        if (e.target.id === "lightbox") fermerLightbox();
    });
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") { fermerLightbox(); fermerModalDetails(); }
    });

    // Modal details
    document.querySelector(".modal-details-fermer").addEventListener("click", fermerModalDetails);
    document.getElementById("modal-details").addEventListener("click", (e) => {
        if (e.target.id === "modal-details") fermerModalDetails();
    });

    // Bouton retour en haut
    const boutonHaut = document.getElementById("retour-haut");
    window.addEventListener("scroll", () => {
        boutonHaut.classList.toggle("visible", window.scrollY > 500);
    });
    boutonHaut.addEventListener("click", () => {
        window.scrollTo({ top: 0, behavior: "smooth" });
    });
});
