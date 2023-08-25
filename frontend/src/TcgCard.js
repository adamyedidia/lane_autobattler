import { Card, CardContent, Typography, Box } from '@mui/material';

function TcgCard({ card, isSelected, onCardClick, onMouseEnter, doNotBorderOnHighlight }) {

    return (
      <div 
          style={{
              border: isSelected ? '2px solid black' : 'none',
              cursor: 'pointer'
          }}
          onClick={onCardClick ? () => onCardClick(card) : null}
          onMouseEnter={e => {
            if (!doNotBorderOnHighlight) {
                e.currentTarget.style.border = '2px solid blue';    
            }
            onMouseEnter && onMouseEnter();
          }}
          onMouseLeave={e => e.currentTarget.style.border = isSelected ? '2px solid black' : 'none'}
      >
        <Card 
        variant="outlined" 
        style={{ 
            width: 250, 
            height: 300, 
            position: 'relative', 
            backgroundColor: '#eee',
            overflow: 'hidden'
        }}
        >
        <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="flex-start">
            <Typography variant="h6">{card.name}</Typography>
            <Typography variant="h6">{card.cost}</Typography>
            </Box>

            <Box mt={2}>
            <Typography variant="body2" color="textSecondary">
                {card.creatureTypes.join(', ')}
            </Typography>
            <Typography>
                Abilities: 
                <ul>
                {card.abilities.map((ability, index) => (
                    <li key={index}>{ability.description}</li>
                ))}
                </ul>
            </Typography>
            </Box>

            <Box 
            position="absolute" 
            bottom={10} 
            right={10} 
            display="flex" 
            alignItems="center"
            >
            <Typography variant="h6" style={{ marginRight: 5 }}>{card.attack}</Typography>
            <Typography variant="h6">{card.health}</Typography>
            </Box>
        </CardContent>
        </Card>
      </div>
    );
    }
  
export default TcgCard;