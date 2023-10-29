export function snakeCase(str) {
    return str.toLowerCase().replace(/[- ]/g, '_').replace(/[\.\']/g, '');
}

export function getCardBackgroundColor(card, isDarkMode) {
    return isDarkMode ? (
        card.creatureTypes.length === 0 ? '#444'
        : card.creatureTypes[0] === 'Fire' ? '#844'
        : card.creatureTypes[0] === 'Water' ? '#448'
        : card.creatureTypes[0] === 'Earth' ? '#484'
        : card.creatureTypes[0] === 'Air' ? '#663'
        : card.creatureTypes[0] === 'Avatar' ? '#848'
        : '#444'
    ) : (
        card.creatureTypes.length === 0 ? '#888' 
        : card.creatureTypes[0] === 'Fire' ? '#f88'
        : card.creatureTypes[0] === 'Water' ? '#aaf'
        : card.creatureTypes[0] === 'Earth' ? '#7d7'
        : card.creatureTypes[0] === 'Air' ? '#ff8'
        : card.creatureTypes[0] === 'Avatar' ? '#f8f'
        : '#888'
    );
}

export function objectToArray(obj) {
    return Object.keys(obj).map(key => obj[key]);
}

export function generateRandomString(length) {
    let result = '';
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    const charactersLength = characters.length;
    for (let i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength));
    }
    return result;
}