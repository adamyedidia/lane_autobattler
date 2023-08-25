import React from 'react';
import { useState, useEffect } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import TcgCard from './TcgCard';
import { URL } from './settings';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import { useTheme } from '@mui/material';


import { Card, CardContent, Grid, Typography } from '@mui/material';

function GameInfo({ game, playerNum, yourManaAmount, opponentManaAmount }) {
    const opponentNum = playerNum === 0 ? 1 : 0;
    const opponentUsername = game.usernames_by_player[opponentNum];
    const opponentHandSize = (game.game_state && game.game_state.hands_by_player) 
                             ? game.game_state.hands_by_player[opponentNum].length 
                             : 0;
    const turnNumber = game?.game_state?.turn || 0;

    return (
        <Card variant="outlined">
            <CardContent>
                <Typography variant="h5" align="left" gutterBottom>
                    Turn {turnNumber}
                    </Typography>
                <Grid container spacing={3}>
                    {/* Your Info Column */}
                    <Grid item xs={6}>
                        <Typography variant="h6">You</Typography>
                        <Typography>Username: {game.usernames_by_player[playerNum]}</Typography>
                        <Typography>Mana: {yourManaAmount}</Typography>
                    </Grid>

                    {/* Opponent Info Column */}
                    <Grid item xs={6}>
                        <Typography variant="h6">Opponent</Typography>
                        <Typography>Username: {opponentUsername}</Typography>
                        <Typography>Hand size: {opponentHandSize}</Typography>
                        <Typography>Mana: {opponentManaAmount}</Typography>
                    </Grid>
                </Grid>
            </CardContent>
        </Card>
    );
}

function CharacterDisplay({ character, setHoveredCard, type }) {
    const theme = useTheme();
    const isDarkMode = theme.palette.mode === 'dark';
    
    const backgroundColor = type === 'player' 
        ? (isDarkMode ? '#226422' : '#d7ffd9')  // darker green for player in dark mode
        : (isDarkMode ? '#995555' : '#ffd7d7'); // darker red for opponent in dark mode

    return (
        <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center', 
            width: '200px', 
            height: '30px',
            border: '1px solid black',
            borderRadius: '5px',
            padding: '5px',
            marginBottom: '5px',
            backgroundColor: backgroundColor,
        }}
          onMouseEnter={e => {
            setHoveredCard(character.template);
          }}>
            <span>{character.template.name}</span>
            <span>{character.current_attack == null ? character.template.attack : character.current_attack}/{character.current_health == null ? character.template.health : character.current_health}</span>
        </div>
    );
}


/*       <div 
style={{
    border: isSelected ? '2px solid black' : 'none',
    cursor: 'pointer'
}}
onClick={onCardClick ? () => onCardClick(card) : null}
onMouseEnter={e => e.currentTarget.style.border = '2px solid blue'}
onMouseLeave={e => e.currentTarget.style.border = isSelected ? '2px solid black' : 'none'}
> */

function LaneCard({ children, selectedCard, onClick }) {
    const outlineStyle = selectedCard ? { outline: '2px solid blue' } : {};
    const theme = useTheme();
    const isDarkMode = theme.palette.mode === 'dark';

    const cardBackgroundColor = isDarkMode ? '#555' : '#eee';

    return (
      <Card
        style={{
          outline: 'none',
          width: '100%',
          padding: '10px',
          backgroundColor: cardBackgroundColor,
          ...outlineStyle,
        }}
        onMouseEnter={e => {
          if (selectedCard) {
            e.currentTarget.style.outline = '2px solid blue';
          }
        }}
        onMouseLeave={e => {
          e.currentTarget.style.outline = 'none';
        }}
        onClick={onClick}
      >
        {children}
      </Card>
    );
  }
  
  function Lane({ laneData, playerNum, opponentNum, selectedCard, setSelectedCard, setLaneData, allLanesData, handData, setHandData, setHoveredCard, cardsToLanes, setCardsToLanes, yourManaAmount, setYourManaAmount }) {
    const laneNumber = laneData.lane_number;
    
    const handleLaneCardClick = () => {
      if (selectedCard) {
        const newLaneData = [...allLanesData];
        newLaneData[laneNumber].characters_by_player[playerNum].push(selectedCard);
        setLaneData(newLaneData);
  
        const newHandData = handData.filter(card => card.id !== selectedCard.id);
        setHandData(newHandData);
  
        setYourManaAmount(yourManaAmount - selectedCard.template.cost);
  
        const newCardsToLanes = { ...cardsToLanes, [selectedCard.id]: laneNumber };
        setCardsToLanes(newCardsToLanes);
  
        setSelectedCard(null);
      }
    };
    
    const renderCharacterCards = (characters, type) => (
      <Card>
        <CardContent>
        <h4>{type === 'opponent' ? "Opponent's" : 'Your'} Score: {laneData.damage_by_player[type === 'opponent' ? opponentNum : playerNum]}</h4>
        {characters.map((card, index) => (
          <CharacterDisplay key={index} character={card} setHoveredCard={setHoveredCard} type={type} />
        ))}
        </CardContent>
      </Card>
    );
  
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', margin: '10px' }}>
        <LaneCard selectedCard={selectedCard} onClick={handleLaneCardClick}>
            <h3>Lane {laneNumber + 1}</h3> {/* +1 assuming lane_number starts from 0 */}
            {renderCharacterCards(laneData.characters_by_player[opponentNum], 'opponent')}
          <br/>
          <div>
            {renderCharacterCards(laneData.characters_by_player[playerNum], 'player')}
          </div>
        </LaneCard>
      </div>
    );
  }
  

function LanesDisplay({ lanes, playerNum, opponentNum, selectedCard, setSelectedCard, setLaneData, handData, setHandData, setHoveredCard, cardsToLanes, setCardsToLanes, yourManaAmount, setYourManaAmount }) {
    return (
        <div style={{ display: 'flex'}}>
        {lanes.map((lane, index) => (
            <Lane 
                key={index} 
                laneData={lane} 
                playerNum={playerNum} 
                opponentNum={opponentNum} 
                selectedCard={selectedCard} 
                setSelectedCard={setSelectedCard}
                setLaneData={setLaneData} 
                allLanesData={lanes}
                handData={handData}
                setHandData={setHandData}
                setHoveredCard={setHoveredCard}
                cardsToLanes={cardsToLanes}
                setCardsToLanes={setCardsToLanes}
                yourManaAmount={yourManaAmount}
                setYourManaAmount={setYourManaAmount}
            />
        ))}
        </div>
    );
}

function HandDisplay({ cards, selectedCard, setSelectedCard, setHoveredCard, yourManaAmount }) {
    return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', marginTop: '20px', flexWrap: 'wrap' }}>
            {cards.map((card, index) => (
                <div key={index} style={{ margin: '5px' }}>
                    <TcgCard 
                        card={card.template} 
                        isSelected={selectedCard ? selectedCard.id === card.id : false} 
                        onMouseEnter={() => setHoveredCard(card.template)} 
                        onCardClick={yourManaAmount >= card.template.cost ? () => setSelectedCard(card) : () => {}} 
                        doNotBorderOnHighlight={yourManaAmount < card.template.cost}
                    />
                </div>
            ))}
        </div>
    );
}

function ResetButton({ onReset, disabled }) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', margin: '10px' }}>
        <Button 
          variant="contained" 
          size="large" 
          onClick={onReset}
          disabled={disabled}
        >
          <Typography variant="h6">
            Reset
          </Typography>
        </Button>
      </div>
    );
  }

  function GameLog({ log }) {
    const theme = useTheme();
    const isDarkMode = theme.palette.mode === 'dark';

    // Define GameLog background color based on theme mode
    const logBackgroundColor = isDarkMode ? '#555' : '#f5f5f5';
    const logTextColor = theme.palette.text.primary;

    const containerStyle = {
        position: 'fixed',
        top: '400px',
        left: '10px',
        width: '250px',
        maxHeight: '300px',
        overflowY: 'auto',
        border: '1px solid black',
        borderRadius: '5px',
        padding: '10px',
        backgroundColor: logBackgroundColor,
        color: logTextColor
    };

    return (
        <div style={containerStyle}>
            {log.map((entry, index) => (
                <p key={index}>{entry}</p>
            ))}
        </div>
    );
}

export default function GamePage({}) {
    const { gameId } = useParams();
    const location = useLocation();
    const queryParams = new URLSearchParams(location.search);
    const playerNum = queryParams.get('playerNum') === "0" ? 0 : 1;
    const opponentNum = playerNum === 0 ? 1 : 0;

    const [game, setGame] = useState({});
    console.log(game);
    const [loading, setLoading] = useState(true);

    const username = localStorage.getItem('username'); // Retrieving username from localStorage

    const [selectedCard, setSelectedCard] = useState(null);
    const [laneData, setLaneData] = useState(null);
    const [handData, setHandData] = useState(null);
    const [hoveredCard, setHoveredCard] = useState(null);
    const [cardsToLanes, setCardsToLanes] = useState({});
    const [dialogOpen, setDialogOpen] = useState(false);

    const [submittedMove, setSubmittedMove] = useState(false);

    const [yourManaAmount, setYourManaAmount] = useState(1);

    const opponentManaAmount = game?.game_state?.mana_by_player?.[opponentNum] || 1;

    console.log(cardsToLanes);

    const handleReset = () => {
        setLaneData(null);
        setSelectedCard(null);
        setHandData(null);
        setCardsToLanes({});
        setYourManaAmount(game?.game_state.mana_by_player?.[playerNum] || 1);
    // If you also want to reset hand data or any other state, do it here.
    };

    const pollApiForGameUpdates = async () => {
        try {
            const response = await fetch(`${URL}/api/games/${gameId}`);
            const data = await response.json();
            
            // Check the data for the conditions you want. For example:
            if (!data.game_state.has_moved_by_player[playerNum]) {
                // Do something based on the response
                // e.g., set some state, or trigger some other effect
    
                // And stop the polling if needed
                setSubmittedMove(false);
                setGame(data);
                handleReset();
                setYourManaAmount(data?.game_state.mana_by_player?.[playerNum] || 1);
            }
        } catch (error) {
            console.error("Error while polling:", error);
            // Depending on the error, you may choose to stop polling
        }
    };

    useEffect(() => {
        let pollingInterval;
    
        if (submittedMove || !game.game_state) {
            pollingInterval = setInterval(pollApiForGameUpdates, 500); // Poll every 0.5 seconds
        }
    
        return () => {
            // This is the cleanup function that will run if the component is unmounted
            // or if the dependencies of the useEffect change.
            if (pollingInterval) {
                clearInterval(pollingInterval);
            }
        };
    }, [submittedMove, !!game.game_state]); // Depend on submittedMove, so the effect re-runs if its value changes

    useEffect(() => {
        // Fetch the game data from your backend.
        fetch(`${URL}/api/games/${gameId}`)
            .then(res => res.json())
            .then(data => {
                setGame(data);
                setLoading(false);
                setLaneData(data.game_state.lanes);
                setYourManaAmount(data?.game_state.mana_by_player?.[playerNum] || 1);
                if (data.game_state.has_moved_by_player[playerNum]) {
                    setSubmittedMove(true);
                }
            })
            .catch(error => {
                console.error("There was an error fetching game data:", error);
            });
    }, [gameId]);

    if (loading) {
        return <div>Loading...</div>;
    }

    if (!game.game_state) {
        return (
            <div >
                <Typography variant="h2" style={{ display: 'flex', justifyContent: 'center'}}>
                    Waiting for another player to join...
                </Typography>
                <Typography variant="h6" style={{ display: 'flex', justifyContent: 'center'}}>
                    Game ID: {gameId}
                </Typography>
            </div>
        )
    }

    const handleOpenDialog = () => {
        setDialogOpen(true);
    };
    
    const handleCloseDialog = () => {
        setDialogOpen(false);
    };
    
    const handleSubmit = () => {
        // Close the dialog first
        handleCloseDialog();
    
        // Construct the payload
        const payload = {
            username: game.usernames_by_player[playerNum], // assuming username is in the local scope
            cardsToLanes: cardsToLanes // adjust as per your setup
        };
    
        // Make the API call
        fetch(`${URL}/api/games/${gameId}/take_turn`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            setSubmittedMove(true);
            // Handle the response as required (e.g. update local state, or navigate elsewhere)
        })
        .catch(error => {
            console.error("There was an error making the submit API call:", error);
        });
    };

    return (
        <div style={{ display: 'flex' }}>
            <div style={{ flex: 1 }}>
                {hoveredCard && <TcgCard card={hoveredCard} doNotBorderOnHighlight={true} />}
            </div>
            <div style={{ flex: 3 }}>
                <div  style={{margin:'10px'}} >
                    <GameInfo game={game} playerNum={playerNum} yourManaAmount={yourManaAmount} opponentManaAmount={opponentManaAmount}/>
                </div>
                <GameLog log={game.game_state.log} />
                <LanesDisplay 
                    lanes={laneData ? laneData : game.game_state.lanes} 
                    playerNum={playerNum} 
                    opponentNum={opponentNum} 
                    selectedCard={selectedCard} 
                    setSelectedCard={setSelectedCard}
                    setLaneData={setLaneData}
                    handData={handData ? handData : game.game_state.hands_by_player[playerNum]}
                    setHandData={setHandData}
                    setHoveredCard={setHoveredCard}
                    cardsToLanes={cardsToLanes}
                    setCardsToLanes={setCardsToLanes}
                    yourManaAmount={yourManaAmount}
                    setYourManaAmount={setYourManaAmount}
                />
                <HandDisplay 
                    cards={handData ? handData : game.game_state.hands_by_player[playerNum]} 
                    selectedCard={selectedCard} 
                    setSelectedCard={setSelectedCard} 
                    setHoveredCard={setHoveredCard}
                    yourManaAmount={yourManaAmount}
                />
                <div style={{ display: 'flex', justifyContent: 'center', margin: '20px' }}>
                    <ResetButton onReset={handleReset} disabled={submittedMove} />
                    <Button variant="contained" color="primary" size="large" style={{margin: '10px'}} onClick={handleOpenDialog} disabled={submittedMove}>
                        <Typography variant="h6">
                            Submit
                        </Typography>
                    </Button>
                </div>

                <Dialog open={dialogOpen} onClose={handleCloseDialog}>
                    <DialogTitle>Confirm Action</DialogTitle>
                    <DialogContent>
                        <DialogContentText>
                            Are you sure you want to submit your turn?
                        </DialogContentText>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={handleCloseDialog} color="primary">
                            Cancel
                        </Button>
                        <Button onClick={handleSubmit} color="primary">
                            Confirm
                        </Button>
                    </DialogActions>
                </Dialog>
            </div>
        </div>
    );
}