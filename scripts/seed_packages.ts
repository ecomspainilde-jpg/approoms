import * as admin from 'firebase-admin';

// Inicializar la app si no está ya inicializada
if (!admin.apps.length) {
    admin.initializeApp();
}

const db = admin.firestore();

/**
 * Script para sembrar la base de datos con los paquetes de precios en Euros
 * Ejecutar con: npx ts-node seed_packages.ts
 */
async function seedPackages() {
    console.log('🌱 Inicializando paquetes de precios en la base de datos...');

    const packages = [
        {
            id: 'pkg_single_render',
            name: 'Render Individual',
            creditsAmount: 1,
            price: 250, // 2.50€ (guardado en céntimos para Stripe)
            currency: 'eur',
            isActive: true,
            description: '1 render en alta calidad. Perfecto para probar.'
        },
        {
            id: 'pkg_pro_renders',
            name: 'Paquete Pro (5 Renders)',
            creditsAmount: 5,
            price: 1000, // 10.00€ -> Sale a 2€ el render
            currency: 'eur',
            isActive: true,
            description: 'Pack de 5 renders. La opción más popular.'
        },
        {
            id: 'pkg_agency_renders',
            name: 'Paquete Agencia (20 Renders)',
            creditsAmount: 20,
            price: 3000, // 30.00€
            currency: 'eur',
            isActive: true,
            description: 'Para profesionales y diseñadores que necesitan volumen diario.'
        }
    ];

    const batch = db.batch();

    for (const pkg of packages) {
        const pkgRef = db.collection('packages').doc(pkg.id);
        batch.set(pkgRef, {
            ...pkg,
            createdAt: admin.firestore.FieldValue.serverTimestamp(),
            updatedAt: admin.firestore.FieldValue.serverTimestamp(),
        });
    }

    try {
        await batch.commit();
        console.log('✅ Paquetes insertados correctamente en Firestore.');
    } catch (error) {
        console.error('❌ Error al insertar los paquetes:', error);
    }
}

// Ejecutar si se llama directamente
if (require.main === module) {
    seedPackages()
        .then(() => process.exit(0))
        .catch(() => process.exit(1));
}
