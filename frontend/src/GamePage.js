import React from 'react';
import { useState, useEffect, useRef } from 'react';
import { resolvePath, useLocation, useParams } from 'react-router-dom';
import TcgCard from './TcgCard';
import { URL } from './settings';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import Divider from '@mui/material/Divider';
import Paper from '@mui/material/Paper';
import { ListItemSecondaryAction, useTheme } from '@mui/material';
import Box from '@mui/material/Box';
import { snakeCase } from './utils';
import { Card, CardContent, Grid, Typography } from '@mui/material';
import battleOld from './battleOld.webp';
import './arrow.css';
import './game_page.css';
import { Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import { dark } from '@mui/material/styles/createPalette';
import { useSocket } from './SocketContext';
import { useNavigate } from 'react-router-dom';
import io from 'socket.io-client';


function log(...args) {
    if (process.env.REACT_APP_LOG != 'false') {
        console.log(...args);
    }
}

const playerColor = (isDarkMode) => isDarkMode ? '#226422' : '#d7ffd9'
const opponentColor = (isDarkMode) => isDarkMode ? '#995555' : '#ffd7d7'

const playerColorToneReversed = (isDarkMode) => isDarkMode ? '#d7ffd9' : '#226422'
const opponentColorToneReversed = (isDarkMode) => isDarkMode ? '#ffd7d7' : '#995555'

const getBackgroundColor = (isDarkMode) => isDarkMode ? '#555' : '#f5f5f5';

function GameInfo({ game, gameState, playerNum, yourManaAmount, opponentManaAmount }) {
    const opponentNum = playerNum === 0 ? 1 : 0;
    const opponentUsername = game.usernames_by_player[opponentNum];
    const opponentHandSize = (gameState && gameState.hands_by_player)
        ? gameState.hands_by_player[opponentNum].length
        : 0;
    const turnNumber = game?.game_state?.turn || 0;

    return (
        <Card variant="outlined">
            <CardContent>
                <Typography variant="h5" align="left" gutterBottom>
                    Turn {turnNumber}
                </Typography>
                <Grid container spacing={1}>
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

function CharacterDisplayOld({ character, setHoveredCard, type }) {
    const theme = useTheme();
    const isDarkMode = theme.palette.mode === 'dark';

    const backgroundColor = type === 'player'
        ? playerColor(isDarkMode)  // darker green for player in dark mode
        : opponentColor(isDarkMode); // darker red for opponent in dark mode

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

const CHARACTER_BOX_WIDTH = '175px';
// const CHARACTER_BOX_WIDTH = 'min(8vw, 12vh)';
const CHARACTER_BOX_HEIGHT = CHARACTER_BOX_WIDTH;

const LANE_WIDTH = `calc(${CHARACTER_BOX_WIDTH} * 2 + 150px)`;
const LANE_HEIGHT = `calc(${CHARACTER_BOX_HEIGHT} * 4 + 325px)`;

const CHARACTER_IMAGE_HEIGHT = `calc(${CHARACTER_BOX_HEIGHT} - 40px)` 
const CHARACTER_IMAGE_WIDTH = `calc(${CHARACTER_BOX_WIDTH} - 10px)`

let characterWidth, characterHeight;

const TOWER_BOX_SIZE = 75;

function CharacterDisplay({ character, setHoveredCard, type , displayArt }) {
    const theme = useTheme();
    const isDarkMode = theme.palette.mode === 'dark';

    const backgroundColor = type === 'player'
        ? playerColor(isDarkMode)  // darker green for player in dark mode
        : opponentColor(isDarkMode); // darker red for opponent in dark mode

    const isDead = character.current_health <= 0;
    let filterStyle = '';
    if (character.shackled_turns > 0) {
        filterStyle += 'brightness(0.5)'; // darken image if shackled_turns is greater than zero
    }


    return (
        <Grid container style={{
            width: CHARACTER_BOX_WIDTH,
            height: CHARACTER_BOX_HEIGHT,
            border: '1px solid black',
            boxSizing: 'border-box',
            borderRadius: '5px',
            padding: '5px',
            backgroundColor: backgroundColor,
            position: 'relative', // Relative positioning to overlay skull
            filter: filterStyle,
        }}
            onMouseEnter={e => {
                setHoveredCard(character.template);
            }}
        >
            {isDead && (
                <img
                    src={'/images/skull.png'}
                    alt="skull-icon"
                    style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        zIndex: 2,
                        maxWidth: '100%',
                        maxHeight: '100%',
                        filter: 'invert(1)',
                    }}
                />
            )}
            <Grid item xs={12}>
                <Box
                    display="flex"
                    justifyContent="space-between"
                    alignItems="center"
                    height="30px">
                    <span>{character.template.name}</span>
                    <span>{character.current_attack == null ? character.template.attack : character.current_attack}/{character.current_health == null ? character.template.health : character.current_health}</span>
                </Box>
            </Grid>
            {displayArt && <Grid item xs={12}>
                <Box
                    display="flex"
                    justifyContent="center"
                    alignItems="flex-end"
                    > 
                    <img
                        src={`/images/${snakeCase(character.template.name)}.png`}
                        alt={`${snakeCase(character.template.name)}-character-art`}
                        style={{ width: CHARACTER_IMAGE_WIDTH, height: CHARACTER_IMAGE_HEIGHT }}
                    />
                </Box>
            </Grid>}
        </Grid>
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

function LaneCard({ children, selectedCard, onClick, doNotOutlineOnHover }) {
    // const outlineStyle = selectedCard ? { outline: '2px solid blue' } : {};
    const outlineStyle = {};
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
                if (selectedCard && !doNotOutlineOnHover) {
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

function OldLane({ laneData, playerNum, opponentNum, selectedCard, setSelectedCard, setLaneData, allLanesData, handData, setHandData, setHoveredCard, cardsToLanes, setCardsToLanes, yourManaAmount, setYourManaAmount }) {
    const laneNumber = laneData.lane_number;

    const handleLaneCardClick = () => {
        if (selectedCard) {
            const newLaneData = JSON.parse(JSON.stringify(allLanesData));
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
                <br />
                <div>
                    {renderCharacterCards(laneData.characters_by_player[playerNum], 'player')}
                </div>
            </LaneCard>
        </div>
    );
}


function OldLanesDisplay({ lanes, playerNum, opponentNum, selectedCard, setSelectedCard, setLaneData, handData, setHandData, setHoveredCard, cardsToLanes, setCardsToLanes, yourManaAmount, setYourManaAmount }) {
    return (
        <div style={{ display: 'flex' }}>
            {lanes.map((lane, index) => (
                <OldLane
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

function HandDisplay({ cards, selectedCard, setSelectedCard, setHoveredCard, yourManaAmount, cardsToMulligan, setCardsToMulligan, mulliganing }) {        
    const toggleMulliganingCard = (card) => {
        if (cardsToMulligan.includes(card.id)) {
            setCardsToMulligan(cardsToMulligan.filter(id => id !== card.id));
        } else {
            setCardsToMulligan([...cardsToMulligan, card.id]);
        }
    };

    return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', marginTop: '20px', flexWrap: 'wrap' }}>
            {cards.map((card, index) => (
                <div key={index} style={{ margin: '5px' }}>
                    <TcgCard
                        card={card.template}
                        isSelected={selectedCard ? selectedCard.id === card.id : false}
                        onMouseEnter={() => setHoveredCard(card.template)}
                        onCardClick={mulliganing ? () => toggleMulliganingCard(card) : yourManaAmount >= card.template.cost ? () => setSelectedCard(card) : () => { }}
                        doNotBorderOnHighlight={yourManaAmount < card.template.cost}
                        displayArt={true}
                        displayRedX={cardsToMulligan.includes(card.id) && mulliganing}
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
    const logBackgroundColor = getBackgroundColor(isDarkMode);
    const logTextColor = theme.palette.text.primary;

    const containerStyle = {
        position: 'fixed',
        bottom: '20px',
        left: '0px',
        width: '250px',
        maxHeight: '300px',
        overflowY: 'auto',
        border: '1px solid black',
        borderRadius: '5px',
        padding: '7px',
        backgroundColor: logBackgroundColor,
        color: logTextColor
    };

    const entryFormatter = (entry) => {
        if (entry.startsWith('Turn '))
            return <Typography variant='h6'> {entry} </Typography>;
        return entry;
    }

    return (
        <div style={containerStyle}>
            {log.map((entry, index) => (
                <p key={index}>{entryFormatter(entry)}</p>
            ))}
        </div>
    );
}

function LanesDisplay({
    lanes,
    playerNum,
    opponentNum,
    selectedCard,
    setSelectedCard,
    setLaneData,
    handData,
    setHandData,
    setHoveredCard,
    cardsToLanes,
    setCardsToLanes,
    yourManaAmount,
    setYourManaAmount,
    characterRefs,
    towerRefs,
    displayArt
}) {
    if (!lanes) return null;
    return (
        <Grid container direction="row" justifyContent="center" spacing={5}>
            {[0, 1, 2].map((i) => (<Grid item style={{ width: LANE_WIDTH, height: LANE_HEIGHT}}>
                <Lane
                    key={i}
                    laneData={lanes[i]}
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
                    characterRefs={characterRefs}
                    towerRefs={towerRefs}
                    displayArt={displayArt}
                />
            </Grid>))}
        </Grid>
    );
}

function LaneForOneSide({
    playersSide,
    laneData,
    playerNum,
    opponentNum,
    selectedCard,
    setSelectedCard,
    setLaneData,
    allLanesData,
    handData,
    setHandData,
    setHoveredCard,
    cardsToLanes,
    setCardsToLanes,
    yourManaAmount,
    setYourManaAmount,
    characterRefs,
    displayArt
}) {
    const laneNumber = laneData.lane_number;

    const lanePlayerNum = playersSide ? playerNum : opponentNum;

    const charactersToRender = laneData.characters_by_player[lanePlayerNum]


    const firstCharacterToRender = charactersToRender?.length > 0 ? charactersToRender?.[0] : null
    const secondCharacterToRender = charactersToRender?.length > 1 ? charactersToRender?.[1] : null
    const thirdCharacterToRender = charactersToRender?.length > 2 ? charactersToRender?.[2] : null
    const fourthCharacterToRender = charactersToRender?.length > 3 ? charactersToRender?.[3] : null

    const paperStyle = {
        height: CHARACTER_BOX_HEIGHT,
        width: CHARACTER_BOX_WIDTH,
        lineHeight: CHARACTER_BOX_HEIGHT,
        textAlign: 'center',
    }

    return (
        <div style={{ maxHeight: '1500px', display: 'flex', flexDirection: 'column', alignItems: 'center', margin: '10px' }}>
            <Grid style={{ display: 'grid', gridTemplateColumns: "repeat(2, 1fr)" }} container direction="row" spacing={1}>
                <Grid item ref={characterRefs?.current?.[laneNumber]?.[lanePlayerNum]?.[0]}>
                    {firstCharacterToRender ? <CharacterDisplay
                        character={firstCharacterToRender}
                        setHoveredCard={setHoveredCard}
                        type={playersSide ? 'player' : 'opponent'}
                        displayArt={displayArt}
                    /> : <Paper style={paperStyle} />}
                </Grid>
                <Grid item ref={characterRefs?.current?.[laneNumber]?.[lanePlayerNum]?.[1]}>
                    {secondCharacterToRender ? <CharacterDisplay
                        character={secondCharacterToRender}
                        setHoveredCard={setHoveredCard}
                        type={playersSide ? 'player' : 'opponent'}
                        displayArt={displayArt}
                    /> : <Paper style={paperStyle} />}
                </Grid>
                <Grid item ref={characterRefs?.current?.[laneNumber]?.[lanePlayerNum]?.[2]}>
                    {thirdCharacterToRender ? <CharacterDisplay
                        character={thirdCharacterToRender}
                        setHoveredCard={setHoveredCard}
                        type={playersSide ? 'player' : 'opponent'}
                        displayArt={displayArt}
                    /> : <Paper style={paperStyle} />}
                </Grid>
                <Grid item ref={characterRefs?.current?.[laneNumber]?.[lanePlayerNum]?.[3]}>
                    {fourthCharacterToRender ? <CharacterDisplay
                        character={fourthCharacterToRender}
                        setHoveredCard={setHoveredCard}
                        type={playersSide ? 'player' : 'opponent'}
                        displayArt={displayArt}
                    /> : <Paper style={paperStyle} />}
                </Grid>
            </Grid>
        </div>
    )
}

function LaneTitle({laneData}) {
    let style = { height: '50px', textWrap: 'wrap', textAlign: 'center' }
    return (
        <><Grid item style={style}>
            <Typography variant="h4" align="center">{laneData.lane_reward.name || 'Lane Title'}</Typography>
        </Grid>
        <Grid item style={style}>
            <Typography variant="h5" align="center">{`${laneData.lane_reward.threshold}: ${laneData.lane_reward.reward_description || 'Lane Description'}`}</Typography>
        </Grid>
        </> 
        )
    }

function Lane({
    laneData,
    playerNum,
    opponentNum,
    selectedCard,
    setSelectedCard,
    setLaneData,
    allLanesData,
    handData,
    setHandData,
    setHoveredCard,
    cardsToLanes,
    setCardsToLanes,
    yourManaAmount,
    setYourManaAmount,
    characterRefs,
    towerRefs,
    displayArt
}) {

    const laneNumber = laneData.lane_number;

    const handleLaneCardClick = () => {
        if (selectedCard && allLanesData[laneNumber].characters_by_player[playerNum].length < 4) {
            const newLaneData = JSON.parse(JSON.stringify(allLanesData));
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

    const isDarkMode = useTheme().palette.mode === 'dark';
    const playerFontColor = playerColorToneReversed(isDarkMode);
    const opponentFontColor = opponentColorToneReversed(isDarkMode);

    return (
        <LaneCard
            selectedCard={selectedCard}
            onClick={handleLaneCardClick}
            doNotOutlineOnHover={allLanesData[laneNumber].characters_by_player[playerNum].length >= 4}
        >
            <Grid container direction="column" spacing={1}>
                <Grid item container direction="row" spacing={1} alignItems="center">
                    <Grid item>
                        <LaneForOneSide
                            playersSide={false}
                            laneData={laneData}
                            playerNum={playerNum}
                            opponentNum={opponentNum}
                            selectedCard={selectedCard}
                            setSelectedCard={setSelectedCard}
                            setLaneData={setLaneData}
                            allLanesData={allLanesData}
                            handData={handData}
                            setHandData={setHandData}
                            setHoveredCard={setHoveredCard}
                            cardsToLanes={cardsToLanes}
                            setCardsToLanes={setCardsToLanes}
                            yourManaAmount={yourManaAmount}
                            setYourManaAmount={setYourManaAmount}
                            characterRefs={characterRefs}
                            displayArt={displayArt}
                        />
                    </Grid>
                    <Grid item> <Card style={{ textAlign: "right", height: '75px', width: '50px', backgroundColor: laneData.earned_rewards_by_player[playerNum] ? playerFontColor : 'backgroundColor' }} ref={towerRefs?.current?.[laneNumber]?.[opponentNum]}>
                        <CardContent style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                            <Typography variant="h4" style={{
                                fontWeight: 'bold',
                                fontFamily: 'Arial',
                                marginTop: '7px',
                                color: laneData.earned_rewards_by_player[playerNum] ? getBackgroundColor(isDarkMode) : playerFontColor,
                            }}>
                                <div>
                                    {laneData.damage_by_player[playerNum]}
                                </div>
                            </Typography>
                        </CardContent>
                    </Card>
                    </Grid>
                </Grid>
                {/* <Grid item>
                <Box 
                    display="flex" 
                    justifyContent="center" 
                    alignItems="center" 
                    height="200px%"  // You can adjust this
                    width="100%"  
                    padding="3px"  // Padding for symmetry
                >
                    <img 
                    src={`/images/${snakeCase(laneData.lane_reward.name)}.png`} 
                    alt={`${snakeCase(laneData.lane_reward.name)}-lane-art`} 
                    style={{
                        maxWidth: '100%', 
                        maxHeight: '100%',
                        // objectFit: 'contain'  // Keeps aspect ratio
                    }}  
                    />
                </Box>
                </Grid> */}
                <LaneTitle laneData={laneData}/>
                <Grid item container direction="row" spacing={1} alignItems="center" textAlign="right">
                    <Grid item>
                        <LaneForOneSide
                            playersSide={true}
                            laneData={laneData}
                            playerNum={playerNum}
                            opponentNum={opponentNum}
                            selectedCard={selectedCard}
                            setSelectedCard={setSelectedCard}
                            setLaneData={setLaneData}
                            allLanesData={allLanesData}
                            handData={handData}
                            setHandData={setHandData}
                            setHoveredCard={setHoveredCard}
                            cardsToLanes={cardsToLanes}
                            setCardsToLanes={setCardsToLanes}
                            yourManaAmount={yourManaAmount}
                            setYourManaAmount={setYourManaAmount}
                            characterRefs={characterRefs}
                            displayArt={displayArt}
                        />
                    </Grid>
                    <Grid item>
                        <Card style={{
                            height: '75px',
                            width: '50px',
                            backgroundColor: laneData.earned_rewards_by_player[opponentNum] ? opponentFontColor : 'backgroundColor'  // conditionally set background color
                        }}
                            ref={towerRefs?.current?.[laneNumber]?.[playerNum]}
                        >
                            <CardContent style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                                <Typography variant="h4" style={{
                                    fontWeight: 'bold',
                                    fontFamily: 'Arial',
                                    marginTop: '7px',
                                    color: laneData.earned_rewards_by_player[opponentNum] ? getBackgroundColor(isDarkMode) : opponentFontColor
                                }}>
                                    <div>
                                        {laneData.damage_by_player[opponentNum]}
                                    </div>
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            </Grid>
        </LaneCard>
    )
}


//   function Lane() {
//     const boxSize = 100; // Change this to set the size of each box

//     return (
//       <Grid container spacing={1}>
//         {/* Create a 4x2 grid */}
//         {Array.from({ length: 6 }, (_, index) => (
//           <Grid item key={index}>
//             <Paper style={{ 
//                 height: `${boxSize}px`, 
//                 width: `${boxSize}px`, 
//                 textAlign: 'center', 
//                 lineHeight: `${boxSize}px`
//               }}>
//               {/* Your character or other content here */}
//             </Paper>
//           </Grid>
//         ))}
//       </Grid>
//     );
//   }

export default function GamePage({ }) {
    const { gameId } = useParams();
    const socket = useSocket();
    window.onload = function () {
        document.body.style.zoom = "67%";
    }
    window.addEventListener('unload', function () {
        socket.emit('leave', { room: gameId });
    });

    const location = useLocation();
    const queryParams = new URLSearchParams(location.search);
    const playerNum = queryParams.get('playerNum') === "0" ? 0 : 1;
    const opponentNum = playerNum === 0 ? 1 : 0;
    const [displayArt, setDisplayArt] = useState(true);

    const [game, setGame] = useState({});
    const [gameState, setGameState] = useState(null);
    log(game);
    log(gameState);
    const [loading, setLoading] = useState(true);

    const username = localStorage.getItem('username'); // Retrieving username from localStorage

    const [selectedCard, setSelectedCard] = useState(null);
    const [laneData, setLaneData] = useState(null);
    const [handData, setHandData] = useState(null);
    const [hoveredCard, setHoveredCard] = useState(null);
    const [cardsToLanes, setCardsToLanes] = useState({});
    const [dialogOpen, setDialogOpen] = useState(false);
    const [cardsToMulligan, setCardsToMulligan] = useState([]);

    const [submittedMove, setSubmittedMove] = useState(false);

    const [yourManaAmount, setYourManaAmount] = useState(1);
    const [animating, setAnimating] = useState(false);

    const ANIMATION_DELAY_STORAGE_KEY = 'animationDelay'
    const BASE_ANIMATION_DELAY = 1600;
    const [animationDelay, setAnimationDelay] = useState(() => {
        // Try to get the value from localStorage or fallback to the default value
        const storedValue = localStorage.getItem(ANIMATION_DELAY_STORAGE_KEY);
        return storedValue ? parseInt(storedValue, 10) : BASE_ANIMATION_DELAY;
    });

    useEffect(() => {
        const f = (event) => {
            if (dialogOpen) {
                if (event.key == 'Enter') {
                    event.preventDefault();
                    handleSubmit();
                } else if (event.key == 'Escape') {
                    event.preventDefault();
                    handleCloseDialog();
                }
            }             
        }

        window.addEventListener('keydown', f);
        return () => window.removeEventListener('keydown', f);
    }, [dialogOpen]);

    const navigate = useNavigate();



    // No longer using this relevantly, originally was gonna not display art on small screens
    function handleResize() {
        setDisplayArt(true);
    }

    useEffect(() => {
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const onRematch = () => {
        const rematchGameId = game?.rematch_game_id;
        let data = {};

        fetch(`${URL}/api/games/${rematchGameId}`).then(response => {
            if (!response.ok) {
                data = {
                    deckId: game?.decks_by_player?.[playerNum].id,
                    hostGameId: rematchGameId,
                    username: game.usernames_by_player[playerNum],
                }
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
                        navigate(`/game/${rematchGameId}?playerNum=0`);
                    })
            }
            else {
                data = {
                    deckId: game?.decks_by_player?.[playerNum].id,
                    gameId: rematchGameId,
                    username: game.usernames_by_player[playerNum],
                }
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
                        navigate(`/game/${rematchGameId}?playerNum=1`); // Redirect to the game page
                    })
            }
        }
        )
    }

    const SPEEDS = [
        { label: '0.5x', value: BASE_ANIMATION_DELAY * 2 },
        { label: '1x', value: BASE_ANIMATION_DELAY },
        { label: '1.5x', value: BASE_ANIMATION_DELAY / 1.5 },
        { label: '2x', value: BASE_ANIMATION_DELAY / 2 },
        { label: '4x', value: BASE_ANIMATION_DELAY / 4 },
        { label: '8x', value: BASE_ANIMATION_DELAY / 8 },
        { label: '16x', value: BASE_ANIMATION_DELAY / 16 },
    ];

    const handleAnimationDelayChange = (event) => {
        const newDelay = event.target.value;
        setAnimationDelay(newDelay);
        localStorage.setItem(ANIMATION_DELAY_STORAGE_KEY, newDelay);
    };

    useEffect(() => {
        const storedValue = localStorage.getItem(ANIMATION_DELAY_STORAGE_KEY);
        if (storedValue) {
            setAnimationDelay(parseFloat(storedValue, 10));
        }
    }, []);
    // Keys are [laneNumber][playerNum][characterNum]
    const characterRefs = useRef({
        0: {
            0: {
                0: React.createRef(),
                1: React.createRef(),
                2: React.createRef(),
                3: React.createRef(),
            },
            1: {
                0: React.createRef(),
                1: React.createRef(),
                2: React.createRef(),
                3: React.createRef(),
            },
        },
        1: {
            0: {
                0: React.createRef(),
                1: React.createRef(),
                2: React.createRef(),
                3: React.createRef(),
            },
            1: {
                0: React.createRef(),
                1: React.createRef(),
                2: React.createRef(),
                3: React.createRef(),
            },
        },
        2: {
            0: {
                0: React.createRef(),
                1: React.createRef(),
                2: React.createRef(),
                3: React.createRef(),
            },
            1: {
                0: React.createRef(),
                1: React.createRef(),
                2: React.createRef(),
                3: React.createRef(),
            },
        },
    });

    const towerRefs = useRef({
        0: {
            0: React.createRef(),
            1: React.createRef(),
        },
        1: {
            0: React.createRef(),
            1: React.createRef(),
        },
        2: {
            0: React.createRef(),
            1: React.createRef(),
        },
    });

    const darkMode = useTheme().palette.mode === 'dark';

    const showArrowFromCharacterToCharacter = (event, arrowType = null) => {
        log(characterRefs)
        log(characterRefs.current)
        log({ ...characterRefs.current })
        log(characterRefs.current[event.attacking_character_id])
        log(event.attacking_character_id)
        log(event);

        let attackingCharacterPos;
        let defendingCharacterPos;

        if (arrowType === 'shackle') {
            attackingCharacterPos = characterRefs?.current?.[event.lane_number]?.[event.player]?.[event.shackling_character_array_index]?.current?.getBoundingClientRect();
        }
        else if (arrowType === 'heal') {
            attackingCharacterPos = characterRefs?.current?.[event.lane_number]?.[event.player]?.[event.healing_character_array_index]?.current?.getBoundingClientRect();
        }
        else {
            attackingCharacterPos = characterRefs?.current?.[event.lane_number]?.[event.attacking_player]?.[event.attacking_character_array_index]?.current?.getBoundingClientRect();
        }
        if (arrowType === 'shackle') {
            defendingCharacterPos = characterRefs?.current?.[event.lane_number]?.[1 - event.player]?.[event.shackled_character_array_index]?.current?.getBoundingClientRect();
        }
        else if (arrowType === 'heal') {
            defendingCharacterPos = characterRefs?.current?.[event.lane_number]?.[event.player]?.[event.healed_character_array_index]?.current?.getBoundingClientRect();
        }
        else {
            defendingCharacterPos = characterRefs?.current?.[event.lane_number]?.[1 - event.attacking_player]?.[event.defending_character_array_index]?.current?.getBoundingClientRect();
        }


        if (!attackingCharacterPos) {
            log('Attacking character position not found!')
            return;
        }

        if (!defendingCharacterPos) {
            log('Defending character position not found!')
            return;
        }

        // slice off the "px"
        characterWidth = CHARACTER_BOX_WIDTH.slice(0, -2);
        characterHeight = CHARACTER_BOX_HEIGHT.slice(0, -2);

        const dx = defendingCharacterPos.left - attackingCharacterPos.left;
        const dy = defendingCharacterPos.top - attackingCharacterPos.top;
        const distance = Math.sqrt(dx * dx + dy * dy);

        // Create an arrow element and set its position and rotation
        const arrow = document.createElement('div');
        arrow.className = 'arrow';
        arrow.style.position = 'absolute'; // Make sure it's set to absolute
        arrow.style.left = `${attackingCharacterPos.left + window.scrollX + characterWidth / 2 + 9}px`;
        arrow.style.top = `${attackingCharacterPos.top + window.scrollY + characterHeight / 2}px`;
        arrow.style.width = `${distance}px`; // Set the length of the arrow

        const angle = Math.atan2(dy, dx) * (180 / Math.PI);
        arrow.style.transform = `rotate(${angle}deg)`;
        arrow.style.transformOrigin = "0 50%";
        if (arrowType === 'shackle') {
            arrow.classList.add("shackled");
        } else if (arrowType === 'heal') {
            arrow.classList.add("healed");
        } else {
            arrow.classList.remove("shackled");
            arrow.classList.remove("healed");
        }

        document.body.appendChild(arrow);

        setTimeout(() => {
            document.body.removeChild(arrow);
        }, animationDelay * 0.67);

        log('Animation successfully triggered!')
    };

    const showArrowFromCharacterToTower = (event) => {
        log(characterRefs)
        log(characterRefs.current[event.attacking_character_id])
        log(event.attacking_character_id)

        log(towerRefs);
        log(event);

        const attackingCharacterPos = characterRefs?.current?.[event.lane_number]?.[event.attacking_player]?.[event.attacking_character_array_index]?.current?.getBoundingClientRect();
        const defendingTowerPos = towerRefs?.current?.[event.lane_number]?.[1 - event.attacking_player]?.current?.getBoundingClientRect();

        if (!attackingCharacterPos) {
            log('Attacking character position not found!')
            return;
        }

        if (!defendingTowerPos) {
            log('Defending tower position not found!')
            return;
        }

        // slice off the "px"
        characterWidth = CHARACTER_BOX_WIDTH.slice(0, -2);
        characterHeight = CHARACTER_BOX_HEIGHT.slice(0, -2);
       
        log(defendingTowerPos, attackingCharacterPos)

        const dx = defendingTowerPos.left + 35 - attackingCharacterPos.left - characterWidth / 2 - 18;
        const dy = defendingTowerPos.top + 37.5 - attackingCharacterPos.top - characterHeight / 2 + (event.attacking_player !== playerNum ? -20 : 8);
        const distance = Math.sqrt(dx * dx + dy * dy);

        // Create an arrow element and set its position and rotation
        const arrow = document.createElement('div');
        arrow.className = 'arrow';
        arrow.style.position = 'absolute'; // Make sure it's set to absolute
        arrow.style.left = `${attackingCharacterPos.left + window.scrollX + characterWidth / 2 + 9}px`;
        arrow.style.top = `${attackingCharacterPos.top + window.scrollY + characterHeight / 2}px`;
        arrow.style.width = `${distance}px`; // Set the length of the arrow

        const angle = Math.atan2(dy, dx) * (180 / Math.PI);
        arrow.style.transform = `rotate(${angle}deg)`;
        arrow.style.transformOrigin = "0 50%";

        document.body.appendChild(arrow);


        setTimeout(() => {
            document.body.removeChild(arrow);
        }, animationDelay * 0.67);

        log('Animation successfully triggered!')
    }

    const highlightRevealingCharacter = (event) => {
        const characterElement = characterRefs?.current?.[event.lane_number]?.[event.player]?.[event.revealing_character_array_index]?.current;

        if (characterElement) {
            // Add the highlighting class
            characterElement.classList.add('highlight-reveal');

            // Remove the highlighting class after 1 second (1000 milliseconds)
            setTimeout(() => {
                characterElement.classList.remove('highlight-reveal');
            }, 1000);
        }
    }

    const opponentManaAmount = gameState?.mana_by_player?.[opponentNum] || 1;

    const gameOver = gameState?.turn > 8;
    const lane1winner = gameState?.lanes?.[0]?.damage_by_player?.[playerNum] > game?.game_state?.lanes?.[0]?.damage_by_player?.[opponentNum];
    const lane2winner = gameState?.lanes?.[1]?.damage_by_player?.[playerNum] > game?.game_state?.lanes?.[1]?.damage_by_player?.[opponentNum];
    const lane3winner = gameState?.lanes?.[2]?.damage_by_player?.[playerNum] > game?.game_state?.lanes?.[2]?.damage_by_player?.[opponentNum];

    const lane1tied = gameState?.lanes?.[0]?.damage_by_player?.[playerNum] === game?.game_state?.lanes?.[0]?.damage_by_player?.[opponentNum];
    const lane2tied = gameState?.lanes?.[1]?.damage_by_player?.[playerNum] === game?.game_state?.lanes?.[1]?.damage_by_player?.[opponentNum];
    const lane3tied = gameState?.lanes?.[2]?.damage_by_player?.[playerNum] === game?.game_state?.lanes?.[2]?.damage_by_player?.[opponentNum];

    const totalFriendlyDamage = gameState?.lanes?.[0]?.damage_by_player?.[playerNum] + gameState?.lanes?.[1]?.damage_by_player?.[playerNum] + gameState?.lanes?.[2]?.damage_by_player?.[playerNum];
    const totalEnemyDamage = gameState?.lanes?.[0]?.damage_by_player?.[opponentNum] + gameState?.lanes?.[1]?.damage_by_player?.[opponentNum] + gameState?.lanes?.[2]?.damage_by_player?.[opponentNum];

    const theme = useTheme();
    const numLanesWon = lane1winner + lane2winner + lane3winner;
    const numLanesTied = lane1tied + lane2tied + lane3tied;
    const numLanesLost = 3 - numLanesWon - numLanesTied;

    let winner = false;
    let tieGame = false;
    if (numLanesWon > numLanesLost) {
        winner = true;
    }
    if (numLanesWon === numLanesLost) {
        if (totalFriendlyDamage > totalEnemyDamage) {
            winner = true;
        }
        if (totalFriendlyDamage === totalEnemyDamage) {
            tieGame = true;
        }
    }

    const triggerAnimations = async (finalGameState, animationQueue) => {
        log('Triggering animations!');
        log(animationQueue);

        for (let [event, newState] of animationQueue) {
            // Trigger the animation based on the event
            log(event.event_type)
            switch (event.event_type) {
                case "start_of_roll":
                    setGameState(newState);
                    break;
                case "character_attack":
                    // Run your animation function, e.g., showArrowToTower(event);
                    log('attacking character');
                    await new Promise((resolve) => setTimeout(resolve, animationDelay)); // 1 second delay
                    showArrowFromCharacterToCharacter(event, null);
                    setGameState(newState);
                    break;
                case "tower_damage":
                    log('attacking tower');
                    await new Promise((resolve) => setTimeout(resolve, animationDelay)); // 1 second delay
                    showArrowFromCharacterToTower(event);
                    setGameState(newState);
                    break;
                case "character_shackle":
                    log('shackling character');
                    await new Promise((resolve) => setTimeout(resolve, animationDelay)); // 1 second delay
                    showArrowFromCharacterToCharacter(event, 'shackle');
                    setGameState(newState);
                    break;
                case "character_heal":
                    log('healing character');
                    await new Promise((resolve) => setTimeout(resolve, animationDelay)); // 1 second delay
                    showArrowFromCharacterToCharacter(event, 'heal');
                    setGameState(newState);
                    break;
                case "on_reveal":
                    log('revealing card');
                    await new Promise((resolve) => setTimeout(resolve, animationDelay)); // 1 second delay
                    highlightRevealingCharacter(event);
                    setGameState(newState);
                    break;
            }

            // Pause execution to let animation complete

            // Update the game state
        }
        await new Promise((resolve) => setTimeout(resolve, animationDelay)); // 1 second delay
        setGameState(finalGameState);
        setAnimating(false);
    };


    const handleReset = () => {
        setLaneData(null);
        setSelectedCard(null);
        setHandData(null);
        setCardsToLanes({});
        setYourManaAmount(gameState?.mana_by_player?.[playerNum] || 1);
        // If you also want to reset hand data or any other state, do it here.
    };

    const pollApiForGameUpdates = async () => {
        try {
            const response = await fetch(`${URL}/api/games/${gameId}`);
            const data = await response.json();

            // Check the data for the conditions you want. For example:
            if (!data.game_state.has_moved_by_player[playerNum]) {
                setSubmittedMove(false);
                setGame(data);
                if (data?.game_state?.animations?.length > 0) {
                    setGameState(data?.game_state?.animations[0][1]);
                }
                else {
                    setGameState(data?.game_state);
                }
                if (!animating && data?.game_state?.animations?.length > 0) {
                    setAnimating(true);
                    triggerAnimations(data?.game_state, data?.game_state?.animations || []);
                }

                handleReset();
                setYourManaAmount(data?.game_state.mana_by_player?.[playerNum] || 1);
            }
            else {
                setGameState(data?.game_state);
            }
        } catch (error) {
            console.error("Error while polling:", error);
            // Depending on the error, you may choose to stop polling
        }
    };
    
    // useEffect(() => {
    //     let pollingInterval;

    //     if (submittedMove || !gameState) {
    //         pollingInterval = setInterval(pollApiForGameUpdates, 500); // Poll every 0.5 seconds
    //     }

    //     return () => {
    //         // This is the cleanup function that will run if the component is unmounted
    //         // or if the dependencies of the useEffect change.
    //         if (pollingInterval) {
    //             clearInterval(pollingInterval);
    //         }
    //     };
    // }, [submittedMove || !gameState]); // Depend on submittedMove, so the effect re-runs if its value changes

    useEffect(() => {
        socket.emit('join', { room: gameId });
        socket.on('update', () => {
            pollApiForGameUpdates();
        })
        pollApiForGameUpdates();
        return () => socket.emit('leave', { room: gameId })
    }, []);

    useEffect(() => {
        // Fetch the game data from your backend.
        log('useEffect fetch');
        fetch(`${URL}/api/games/${gameId}`)
            .then(res => res.json())
            .then(data => {
                setGame(data);
                setGameState(data?.gameState);
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

    if (!gameState) {
        return (
            <div >
                <Typography variant="h2" style={{ display: 'flex', justifyContent: 'center' }}>
                    Waiting for another player to join...
                </Typography>
                <Typography variant="h6" style={{ display: 'flex', justifyContent: 'center' }}>
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

    const mulliganing = !gameState.has_mulliganed_by_player[playerNum]

    const handleSubmit = () => {
        // Close the dialog first
        handleCloseDialog();

        if (mulliganing) {
            const payload = {
                username: game.usernames_by_player[playerNum],
                cards: cardsToMulligan,
            };

            fetch(`${URL}/api/games/${gameId}/mulligan`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                })
                .then(response => response.json())
                .then(data => {
                    console.log(data);
                    setGame(data.game);
                    setGameState(data.game.game_state);
                    // Handle the response as required (e.g. update local state, or navigate elsewhere)
                })
            }
        else {

            const payload = {
                username: game.usernames_by_player[playerNum],
                cardsToLanes: cardsToLanes,
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
                    log(data);
                    setSubmittedMove(true);
                    // Handle the response as required (e.g. update local state, or navigate elsewhere)
                })
                .catch(error => {
                    console.error("There was an error making the submit API call:", error);
                });                
            }
        };

    return (
        <div style={{
            display: 'flex',
            backgroundImage: `url(${battleOld})`,
            backgroundSize: 'cover',  // Cover the entire container
            backgroundRepeat: 'no-repeat',
            backgroundPosition: 'center center',
            height: '100%', 
            width: '100%', 
        }}>
            <div style={{ flex: 1 }}>
                {hoveredCard && <TcgCard card={hoveredCard} doNotBorderOnHighlight={true} displayArt />}
            </div>
            <div style={{ flex: 10 }}>
                <div style={{margin: '1px'}}>
                    <GameInfo
                        game={game}
                        gameState={gameState}
                        playerNum={playerNum}
                        yourManaAmount={yourManaAmount}
                        opponentManaAmount={opponentManaAmount}
                        />
                </div>
                {gameOver && !animating && <div style={{ margin: '10px' }}>
                    <Card variant="outlined">
                        <CardContent>
                            <Typography variant="h2" style={{ display: 'flex', justifyContent: 'center' }}>
                                {tieGame ? 'You tied!' : winner ? 'You won!' : 'You lost!'}
                            </Typography>
                        </CardContent>
                    </Card>
                </div>}
                {mulliganing && <div style={{ margin: '10px' }}>
                    <Card variant="outlined">
                        <CardContent>
                            <Typography variant="h2" style={{ display: 'flex', justifyContent: 'center' }}>
                                Pick which cards to mulligan
                            </Typography>
                        </CardContent>
                    </Card>
                </div>}                
                <GameLog log={gameState.log} />
                <FormControl style={{
                    margin: '1px',
                    minWidth: 120,
                    position: 'fixed',
                    bottom: '20px',
                    left: '270px',
                }}>
                    <InputLabel id="animation-speed-label">Animation Speed</InputLabel>
                    <Select
                        labelId="animation-speed-label"
                        id="animation-speed-select"
                        value={animationDelay}
                        onChange={handleAnimationDelayChange}
                        style={{
                            marginTop: theme.spacing(1),
                            backgroundColor: getBackgroundColor(darkMode),
                        }}
                    >
                        {SPEEDS.map((speed, index) => ( 
                            <MenuItem key={index} value={speed.value}>
                                {speed.label}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
                {/* <Select> */}
                    {/* <MenuItem value={BASE_ANIMATION_DELAY} onClick={() => setAnimationDelay(BASE_ANIMATION_DELAY)}>Normal</MenuItem> */}
                {/* </Select> */}
                {/* <OldLanesDisplay 
                    lanes={laneData ? laneData : gameState.lanes} 
                    playerNum={playerNum} 
                    opponentNum={opponentNum} 
                    selectedCard={selectedCard} 
                    setSelectedCard={setSelectedCard}
                    setLaneData={setLaneData}
                    handData={handData ? handData : gameState.hands_by_player[playerNum]}
                    setHandData={setHandData}
                    setHoveredCard={setHoveredCard}
                    cardsToLanes={cardsToLanes}
                    setCardsToLanes={setCardsToLanes}
                    yourManaAmount={yourManaAmount}
                    setYourManaAmount={setYourManaAmount}
                /> */}
                <LanesDisplay
                    lanes={laneData ? laneData : gameState.lanes}
                    playerNum={playerNum}
                    opponentNum={opponentNum}
                    selectedCard={selectedCard}
                    setSelectedCard={setSelectedCard}
                    setLaneData={setLaneData}
                    handData={handData ? handData : gameState.hands_by_player[playerNum]}
                    setHandData={setHandData}
                    setHoveredCard={setHoveredCard}
                    cardsToLanes={cardsToLanes}
                    setCardsToLanes={setCardsToLanes}
                    yourManaAmount={yourManaAmount}
                    setYourManaAmount={setYourManaAmount}
                    characterRefs={characterRefs}
                    towerRefs={towerRefs}
                    displayArt={displayArt}
                />
                <HandDisplay
                    cards={handData ? handData : gameState.hands_by_player[playerNum]}
                    selectedCard={selectedCard}
                    setSelectedCard={setSelectedCard}
                    setHoveredCard={setHoveredCard}
                    yourManaAmount={yourManaAmount}
                    cardsToMulligan={cardsToMulligan}
                    setCardsToMulligan={setCardsToMulligan}
                    mulliganing={mulliganing}
                />
               <div
                    style={{
                        position: 'fixed',
                        bottom: '20px',
                        right: '20px',
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center'
                    }}
                >
                    {gameOver && !animating && <Button variant="contained" color="primary" size="large" style={{ margin: '10px' }} onClick={onRematch}>Rematch</Button>}
                    {!gameOver && !mulliganing && <ResetButton onReset={handleReset} disabled={submittedMove || gameOver} />}
                    {!gameOver && <Button variant="contained" color="primary" size="large" style={{ margin: '10px' }} onClick={mulliganing ? handleSubmit : handleOpenDialog} disabled={submittedMove || gameOver}>
                        <Typography variant="h6">
                            {mulliganing ? 'Submit mulligan' : 'Submit'}
                        </Typography>
                    </Button>}
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