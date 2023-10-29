import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
  TextField,
  Button,
  List,
  Typography,
  Grid,
  Snackbar,
  Alert,
  Box,
  CardContent,
  Card,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  MenuItem,
  Select,
  Menu,
  Checkbox,
  FormControlLabel,
} from '@mui/material';
import TcgCard from './TcgCard';

import { URL } from './settings';
import { useNavigate } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { objectToArray } from './utils';
import { useSocket } from './SocketContext';
import LaneRewardDisplay from './LaneRewardDisplay';
import Timer from './Timer';


const calculateManaCurve = (deck, cards) => {
  const manaCurve = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0};
  deck.forEach(cardName => {
      const card = cards.find(c => c.name === cardName);
      if (card && card.cost !== undefined) {
          if (manaCurve[card.cost]) {
              manaCurve[card.cost]++;
          } else {
              manaCurve[card.cost] = 1;
          }
      }
  });
  return manaCurve;
};

function DraftComponent({ cardPool, setCurrentDeck, currentDeck, setDrafting, saveDeck, currentLaneReward, setCurrentLaneReward, isTimedDraft, draftStartTime }) {
  const [draftOptions, setDraftOptions] = useState([]);
  const [secondsElapsed, setSecondsElapsed] = useState(null);
  const [timerHasElapsed, setTimerHasElapsed] = useState(false);

  const [currentDeck2, setCurrentDeck2] = useState([]);

  const currentDeckRef = useRef(currentDeck);

  const DRAFT_DECK_SIZE = 18;

  useEffect(() => {
    currentDeckRef.current = currentDeck;
  }, [currentDeck]);

  useEffect(() => {
    // Function to generate four distinct random cards from cardPool
    const fetchDraftOptions = () => {
      let randomCards = [];

      const data = {
        username: localStorage.getItem('userName'),
        lastCardOptions: draftOptions.map(card => card.name),
        lastCardPicked: currentDeck.length > 0 ? currentDeck[currentDeck.length - 1] : null,
      }

      fetch(`${URL}/api/draft_pick?pickNum=${currentDeck.length + 1}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      })
      .then(response => response.json())
      .then((data) => {
          setDraftOptions(data.options);
      })
      .catch((error) => {
          console.error('Error fetching open games:', error);
      });
      return randomCards;
    };

    if (currentDeck.length < DRAFT_DECK_SIZE) {
      fetchDraftOptions();

      // setDraftOptions(getRandomCards());
    }
    else {
      saveDeck(`Draft deck with ${currentDeck[0]} and ${currentDeck[1]}`, currentLaneReward.name);
      setDrafting(false);
      setCurrentLaneReward(null);
    }

  }, [currentDeck]);

  const addToDeck = (cardName) => {
    setCurrentDeck(prev => [...prev, cardName]);
  };

  const fillDeckWithRandomCards = () => {
    const currentDeck = currentDeckRef.current;
    const numCardsToAdd = DRAFT_DECK_SIZE - currentDeck.length;
    const randomCards = [];
    while (randomCards.length < numCardsToAdd) {
      const randomCard = cardPool[Math.floor(Math.random() * cardPool.length)];
      randomCards.push(randomCard.name);
    }
    // setCurrentDeck(prev => [...prev, ...randomCards]);
    let deckName = 'Random draft deck';
    if (currentDeck.length > 1) {
      deckName = `Draft deck with ${currentDeck[0]} and ${currentDeck[1]}`;
    }
    saveDeck(deckName, currentLaneReward.name, [...currentDeck, ...randomCards]);
    setDrafting(false);
    setCurrentLaneReward(null);
  };

  const onTimerElapsed = () => {
    if (timerHasElapsed) return;
    setTimerHasElapsed(true);
    fillDeckWithRandomCards();
  }

  // const onTimerElapsed = () => {};

  if (currentDeck.length === DRAFT_DECK_SIZE) return null;

  return (
    <React.Fragment>
      <Grid container direction="column" spacing={1}>
        {isTimedDraft && draftStartTime && <Grid item>
          <Timer 
            lastTimerStart={draftStartTime / 1000} 
            secondsPerTurn={240}
            secondsElapsed={secondsElapsed}
            setSecondsElapsed={setSecondsElapsed}
            doNotUpdateTimer={false}
            onTimerElapsed={onTimerElapsed}
            currentDeck={currentDeck}
          />
        </Grid>}
        <Grid item xs={4}>
          <Typography variant="h6">Your games will contain the following lane:</Typography>
          <LaneRewardDisplay
            laneReward={currentLaneReward}
            currentLaneReward={currentLaneReward}
            setCurrentLaneReward={setCurrentLaneReward}
            notSelectable={true}
          />
        </Grid>
        <Grid item>
          <Typography variant="h6">Drafting card {currentDeck.length + 1}/{DRAFT_DECK_SIZE}</Typography>
        </Grid>
        <Grid item>
          <Grid container spacing={3}>
            {draftOptions.map((card) => (
              <Grid item key={card.name} xs={12} sm={6} md={4} lg={3} onClick={() => addToDeck(card.name)}>
                <TcgCard card={card} doNotBorderOnHighlight={true} displayArt />
              </Grid>
            ))}
          </Grid>
        </Grid>
      </Grid>
    </React.Fragment>
  );
}


function TcgCardListItem({ cardName, index, removeFromDeck, doNotAllowDeleting, setHoveredCard  }) {
  return (
    <ListItem 
      component={Box} 
      borderColor="grey.300" 
      border={1} 
      borderRadius={4} 
      style={{ marginBottom: '8px' }}
      onMouseEnter={() => setHoveredCard(cardName)}
      onMouseLeave={() => setHoveredCard(null)}
    >
        <ListItemText primary={cardName} />
        {!doNotAllowDeleting && <ListItemSecondaryAction>
            <IconButton edge="end" aria-label="delete" onClick={() => removeFromDeck(index)}>
              ❌
            </IconButton>
        </ListItemSecondaryAction>}
    </ListItem>
  )
}

function toUrlParams(obj) {
  return Object.keys(obj).map(key => `${key}=${obj[key]}`).join('&');
}


function DeckBuilder({ cards, laneRewards }) {
  const [currentDeck, setCurrentDeck] = useState([]);
  const [decks, setDecks] = useState([]);
  const [userName, setUserName] = useState(localStorage.getItem('userName') || ''); // Retrieve from localStorage
  const [deckName, setDeckName] = useState('');
  const [toastOpen, setToastOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [selectedDeck, setSelectedDeck] = useState(null); // For highlighting the selected deck

  const [hostGameId, setHostGameId] = useState(''); // For displaying gameId
  const [joinGameId, setJoinGameId] = useState(''); // For entering gameId
  const [drafting, setDrafting] = useState(false);
  const [currentLaneReward, setCurrentLaneReward] = useState(null);
  const [openGames, setOpenGames] = useState([]);
  const [timeControl, setTimeControl] = useState(parseInt(localStorage.getItem('timeControl')) || -1); // You can set a default value, for instance, 5 seconds for Hyperbullet

  const [hoveredCard, setHoveredCard] = useState(null);

  const navigate = useNavigate();

  const manaCurve = calculateManaCurve(currentDeck, cards);
  const socket = useSocket();

  const [isTimedDraft, setIsTimedDraft] = useState(localStorage.getItem('isTimedDraft') || false);
  const [draftStartTime, setDraftStartTime] = useState(null);

  console.log(laneRewards);

  console.log(selectedDeck);

  const hostGame = (botGame, botDifficulty) => {
    const data = {
      deckId: selectedDeck.id, // Assuming each deck object has an 'id' property
      username: userName,
      bot_game: botGame,
      bot_difficulty: botDifficulty,
      secondsPerTurn: timeControl === -1 ? null : timeControl,
    };

    fetch(`${URL}/api/host_game`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
    .then(response => {
      if (!response.ok) {
        return response.json().then(data => {
          throw new Error(data.error);
        });
      }
      return response.json();
    })
    .then(data => {
      setHostGameId(data.gameId); // Display the received gameId
      navigate(`/game/${data.gameId}?playerNum=0`);
      window.location.reload();
    })
    .catch(error => {
      setErrorMessage(error.message);
      setToastOpen(true);
    });
  };

  const joinGame = (submittedGameId) => {
    const gameIdToJoin = submittedGameId || joinGameId;

    console.log(`Joining ${gameIdToJoin}`)

    const data = {
      deckId: selectedDeck.id,
      username: userName,
      gameId: gameIdToJoin,
      rand: Math.random(), // To prevent caching
    };

    fetch(`${URL}/api/join_game`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
    .then(response => {
      if (!response.ok) {
        return response.json().then(data => {
          throw new Error(data.error);
        });
      }
      // Handle successful join, if necessary
    })
    .then(() => {
      navigate(`/game/${gameIdToJoin}?playerNum=1`); // Redirect to the game page
      window.location.reload();
    })
    .catch(error => {
      setErrorMessage(error.message);
      setToastOpen(true);
    });
  };  

  useEffect(() => {
    // Fetch decks and other initial setup

    // Set the userName in localStorage whenever it changes
    localStorage.setItem('userName', userName);
  }, [userName]);

  useEffect(() => {
    // Set the timeControl in localStorage whenever it changes
    localStorage.setItem('timeControl', timeControl);
  }, [timeControl]);

  useEffect(() => {
    // Set the timeControl in localStorage whenever it changes
    localStorage.setItem('isTimedDraft', isTimedDraft);
  }, [isTimedDraft]);

  const fetchDecks = () => {
    fetch(`${URL}/api/decks?username=${userName}&rand=${Math.random()}}`)
      .then(response => response.json())
      .then(data => setDecks(data))
      .catch(error => {
        setErrorMessage("Failed to fetch decks.");
        setToastOpen(true);
      });
  }

  useEffect(fetchDecks, [userName]);

  const fetchAvailableGames = () => {
    fetch(`${URL}/api/open_games?username=${userName}`)
      .then(response => response.json())
      .then((data) => {
          console.log(data);
          setOpenGames(data?.games || []);
      })
      .catch((error) => {
          console.error('Error fetching open games:', error);
      });
  }

  useEffect(() => {
    fetchAvailableGames();
    socket.on('updateGames', () => {
      console.log('update games received')
      fetchAvailableGames();
  })
}, []);

  const addToDeck = (cardName) => {
    setCurrentDeck([...currentDeck, cardName]);
  };

  const saveDeck = (deckName, laneRewardName, deckArray) => {
    const deckData = {
      name: deckName,
      username: userName,
      cards: deckArray ? deckArray : currentDeck,
      laneRewardName: laneRewardName || null,
    };

    fetch(`${URL}/api/decks`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(deckData)
    })
    .then(response => {
      if (!response.ok) {
        return response.json().then(data => {
          throw new Error(data.error);
        });
      }
      return response.json();
    })
    .then(data => {
      setDecks(prevDecks => [...prevDecks, data]); // Assuming your backend returns the saved deck
      setCurrentDeck([]);
      setDeckName('');
    })
    .catch(error => {
      setErrorMessage(error.message);
      setToastOpen(true);
    });
  };

  const handleDeleteDeck = (deck) => {
    // deck_name = request.args.get('deckName')
    // username = request.args.get('username')
    // deck_id = request.args.get('deckId')

    console.log(deck);

    const deckData = {
      deckName: deck.name,
      username: userName,
      deckId: deck.id,
    };

    fetch(`${URL}/api/decks?${toUrlParams(deckData)}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      },
    })
    .then(response => {
      if (!response.ok) {
        return response.json().then(data => {
          throw new Error(data.error);
        });
      }
      setDecks(prevDecks => prevDecks.filter(d => d.id !== deck.id));
    })
    .catch(error => {
      setErrorMessage(error.message);
      setToastOpen(true);
    });
  };

  const handleCloseToast = () => {
    setToastOpen(false);
  };

  const removeFromDeck = (index) => {
    setCurrentDeck(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <>
    <br />
    <Container>
      <Card>
          <CardContent>
            <Typography variant="h5">Recent changes:</Typography>
            <ul>
              <li>Attackers no longer attack both an enemy character and an enemy tower by default. Instead, they only attack an enemy character. They also attack the enemy tower if they have the "Twinstrike" ability. Only attackers ever have Twinstrike.</li>
              <li>Characters can have a shield; this means that the next instance of damage is negated and the shield is lost instead. The Shield ability means it gains a shield when it enters the lane.</li>
              <li>When you <emph>silence</emph> a character, that character permanently loses all its abilities, its attack reverts to its original base attack, its base health reverts to its original base health, and its current health reverts to whichever is smaller of its original base health and its current health, and any shield it has is broken.</li>
              <li>The same character can no longer be shackled several times. Shackles never last more than one turn.</li>
              <li>Characters that switch lanes can attack several times if they switch rightwards. This was not true for a bit but is back to being true.</li>
              <li>There is no more final battle. After turn 8, there's one fight, and then the game ends.</li>
              <li>Whichever side has more characters in a given lane attacks first. If both sides have the same number of characters, the side that attacks first is random.</li>
              <li>Characters always attack in reading order now (i.e. the upper-left character attacks first, then the upper-right character, then the lower-left character, etc). This order corresponds to the order in which those characters entered the lane. For this reason, the order in which you play cards into a lane on a single turn can matter.</li>
              <li>A bunch of card wording has been cleaned up, and instanced of "in this lane" have been removed. It's still the case that by default, characters only "see" and affect things in their own lane, unless explicitly said otherwise.</li>
            </ul>
          </CardContent>
      </Card>
      <br />
      <Card>
          <CardContent>
            <Typography variant="h5">Deck Builder</Typography>
            <TextField 
                label="User Name" 
                variant="outlined" 
                margin="normal"
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
              />
            </CardContent>
        </Card>

  <br></br>
  <Grid container spacing={2}>
    <Grid item xs={selectedDeck ? 4 : 8}>
      <Card>
        <CardContent>
        <Typography variant="h6" style={{ marginTop: '20px' }}>All Your Decks:</Typography>
          {decks.map((deck, index) => (
            <>
            <Grid container direction="row" spacing={1}>
              <Grid item>
            <Box 
              key={index}
              component="button"
              display="block"
              border={deck === selectedDeck ? "2px solid #3f51b5" : "none"} // Highlight if selected
              borderRadius="4px"
              padding="10px"
              margin="5px 0"
              textAlign="left"
              onClick={() => setSelectedDeck(deck)}
            >
              {deck.name}
            </Box>
            </Grid>
            <Grid item>
              {deck.username !== 'COMMON_DECK' && <IconButton edge="end" aria-label="delete" onClick={() => handleDeleteDeck(deck)}>
                ❌
              </IconButton>}
            </Grid>
          </Grid>
          </>
          ))}
          {/* Host and Join game actions */}
          <Grid container spacing={2} alignItems="center" style={{ marginTop: '20px' }}>
            <Grid item>
              <Typography variant="body1">Time control for hosted game:</Typography>
            </Grid>
            <Grid item>
              <Select
                value={timeControl}
                onChange={(e) => setTimeControl(e.target.value)}
                variant="outlined"
                style={{ minWidth: '150px' }} // set a minimum width to accommodate longer names
              >
                <MenuItem value={-1}>None</MenuItem>
                <MenuItem value={5}>Hyperbullet</MenuItem>
                <MenuItem value={10}>Bullet</MenuItem>
                <MenuItem value={20}>Blitz</MenuItem>
                <MenuItem value={30}>Rapid</MenuItem>
                <MenuItem value={45}>Standard</MenuItem>
                <MenuItem value={60}>Slow</MenuItem>
                <MenuItem value={90}>Classical</MenuItem>
              </Select>
            </Grid>
          </Grid>

          <Grid container spacing={2} alignItems="center" style={{ marginTop: '20px' }}>
            <Grid item>
              <Button variant="contained" color="primary" onClick={() => hostGame(false)} disabled={!selectedDeck}>
                {selectedDeck ? 'Host Game' : 'Select Deck'}
              </Button>
            </Grid>
            <Grid item>
              <Button variant="contained" color="primary" onClick={() => hostGame(true, 'goldfish')} disabled={!selectedDeck}>
                {selectedDeck ? 'Play vs. goldfish' : 'Select Deck'}
              </Button>
            </Grid>            
            <Grid item>
              <Button variant="contained" color="primary" onClick={() => hostGame(true, 'easy')} disabled={!selectedDeck}>
                {selectedDeck ? 'Play vs. bot (easy)' : 'Select Deck'}
              </Button>
            </Grid>
            <Grid item>
              <Button variant="contained" color="primary" onClick={() => hostGame(true)} disabled={!selectedDeck}>
                {selectedDeck ? 'Play vs. bot (hard)' : 'Select Deck'}
              </Button>
            </Grid>
            <Grid item>
              {/* Display Game ID when hosting a game */}
              {hostGameId && (
                <Typography variant="h6" style={{ marginTop: '20px' }}>
                  Game ID: <Link to={`/game/${hostGameId}?playerNum=0`}>{hostGameId}</Link>
                </Typography>
              )}
            </Grid>
            </Grid>

          <Grid container spacing={2} alignItems="center" style={{ marginTop: '20px' }}>
            <Grid item>
              <TextField 
                variant="outlined"
                label="Game ID"
                value={joinGameId}
                onChange={(e) => setJoinGameId(e.target.value)}
              />
            </Grid>
            <Grid item>
              <Button variant="contained" color="secondary" onClick={() => joinGame()} disabled={!selectedDeck}>
                {selectedDeck ? 'Join Game' : 'Select Deck'}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Grid>

    {selectedDeck && (<Grid item xs={4}>
      <Card>
        <CardContent>
          <Typography variant="h5">Selected deck:</Typography>
          <br />
          <Typography variant="h6">{selectedDeck.name}</Typography>
          <br />
          {selectedDeck.associated_lane_reward_name && <LaneRewardDisplay
            laneReward={laneRewards[selectedDeck.associated_lane_reward_name]}
            currentLaneReward={null}
            setCurrentLaneReward={() => {}}
            notSelectable={true}
          />}
          <br />
          {selectedDeck.card_templates.map((cardTemplate, index) => (
            <TcgCardListItem
              key={index}
              cardName={cardTemplate.name}
              index={index}
              doNotAllowDeleting={true}
              setHoveredCard={setHoveredCard}
            />
          ))}
        </CardContent>
      </Card>
    </Grid>)}

    <Grid item xs={4}>
    <Card>
              <CardContent>
                  {selectedDeck ? <Typography variant="h6">Open Games:</Typography> : <Typography variant="h6">Select a deck</Typography>}
                  {openGames.map((game, index) => (
                      <Box 
                          key={index}
                          display="block"
                          borderRadius="4px"
                          padding="10px"
                          margin="5px 0"
                          textAlign="left"
                      >
                        <Button onClick={() => joinGame(game.id)} disabled={!selectedDeck} variant="contained">
                          {`${game.player_0_username}'s game`}
                        </Button>
                      </Box>
                  ))}
              </CardContent>
          </Card>
      </Grid>
  </Grid>      

  {/*space between the two cards*/}
  <br></br>

  {/* A card with the title create a new deck 
  that contains a text feild and create deck button */}
<Card>
  <CardContent>
    <Typography variant="h6" style={{ marginTop: '20px' }}>Create a New Deck:</Typography>
    
    <Grid container alignItems="center" spacing={2}>
      <Grid item>
        <TextField 
          label="Deck Name" 
          variant="outlined" 
          value={deckName}
          onChange={(e) => setDeckName(e.target.value)}
        />
      </Grid>
      
      <Grid item>
        <Button 
          variant="contained" 
          color="primary" 
          onClick={() => saveDeck(deckName, currentLaneReward?.name)}
          disabled={!userName || !deckName || !currentDeck || currentDeck.length === 0}>
          {!userName ? 'Enter User Name' : !deckName ? 'Enter Deck Name' : !currentDeck || currentDeck.length === 0 ? 'Add Cards to Deck' : 'Save Deck'}
        </Button>
      </Grid>
    </Grid>
    </CardContent>

    <CardContent>
    <Typography variant="h6">Deck You Are Building:</Typography>
      <Box style={{ maxWidth: '200px', alignItems: 'flex-start' }}>
        <List>
            {currentDeck.map((cardName, index) => (
              <TcgCardListItem
                key={index}
                cardName={cardName}
                index={index}
                removeFromDeck={removeFromDeck}
                doNotAllowDeleting={drafting}
                setHoveredCard={setHoveredCard}
              />
            ))}
        </List>
      </Box>
  </CardContent>

  {currentDeck && currentDeck.length > 0 && <CardContent>
      <Typography variant="h6">Mana Curve:</Typography>
      <Box display="flex" alignItems="flex-end" height={200}>
          {Object.keys(manaCurve).sort((a, b) => parseInt(a) - parseInt(b)).map(mana => (
              <Box key={mana} m={1} display="flex" flexDirection="column" alignItems="center">
                  <Box bgcolor="blue" width={50} height={`${manaCurve[mana] * 20}px`}></Box>
                  <Typography variant="body1">{mana}</Typography>
              </Box>
          ))}
      </Box>
    </CardContent>}

  {hoveredCard && (
    <Box position="fixed" top="10px" right="10px" zIndex={10}>
        <TcgCard card={cards.find(card => card.name === hoveredCard)} doNotBorderOnHighlight={true} doNotShowPointerCursor={true} displayArt />
    </Box>
  )}

  {!drafting && <CardContent>
    <Grid container direction="row" spacing={3}>
      <Grid item>
        <Button variant="outlined" onClick={() => {
            const laneRewardsArray = objectToArray(laneRewards);
            setDrafting(true);
            setCurrentDeck([]);
            setCurrentLaneReward(laneRewardsArray[Math.floor(Math.random() * laneRewardsArray.length)]);
            if (isTimedDraft) {
              setDraftStartTime(Date.now());
            }
        }}>
          Draft Cards
        </Button>
      </Grid>
      <Grid item>
        <FormControlLabel 
          control={
            <Checkbox 
              checked={isTimedDraft} 
              onChange={(e) => setIsTimedDraft(e.target.checked)} 
              name="timedDraftCheckbox" 
            />
          } 
          label="Timed draft" 
        />
      </Grid>
    </Grid>
  </CardContent>}

  {drafting && <CardContent>
    <DraftComponent 
      cardPool={cards.filter((card) => !card?.notInCardPool)} 
      setCurrentDeck={setCurrentDeck} 
      currentDeck={currentDeck} 
      setDrafting={setDrafting} 
      saveDeck={saveDeck} 
      currentLaneReward={currentLaneReward}
      setCurrentLaneReward={setCurrentLaneReward}
      isTimedDraft={isTimedDraft}
      draftStartTime={draftStartTime}
    />
  </CardContent>}

  {!drafting && <CardContent>
     <Typography variant="h6" style={{ marginTop: '20px' }}>Available Cards:</Typography>
      <Grid container spacing={3}>
        {cards.map((card) => (
          card?.notInCardPool ? null : <Grid item key={card.name} xs={12} sm={6} md={4} lg={3} onClick={() => addToDeck(card.name)}>
            <TcgCard card={card} doNotBorderOnHighlight={true} displayArt />
          </Grid>
        ))}
      </Grid>
  </CardContent>}

  {!drafting && <CardContent>
     <Typography variant="h6" style={{ marginTop: '20px' }}>Available Lanes:</Typography>
      <Grid container spacing={3}>
        {objectToArray(laneRewards).map((laneReward) => (
          <Grid item key={laneReward.name} xs={12} sm={6} md={4} lg={3}>
            <LaneRewardDisplay laneReward={laneReward} currentLaneReward={currentLaneReward} setCurrentLaneReward={setCurrentLaneReward} />
          </Grid>
        ))}
      </Grid>
  </CardContent>}
</Card>
      

      <Snackbar 
        open={toastOpen}
        autoHideDuration={6000}
        onClose={handleCloseToast}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseToast} severity="error" variant="filled">
          {errorMessage}
        </Alert>
      </Snackbar>
    </Container>
    </>
  );
}

export default DeckBuilder;