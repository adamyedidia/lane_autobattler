import React, { useEffect, useState } from 'react';
import { URL } from './settings';
import TcgCard from './TcgCard';
import { Typography } from '@mui/material';
import { Grid } from '@mui/material';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import { formatPercentage } from './utils';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TableSortLabel, Paper } from '@mui/material';

export const getOrganizedCardPool = (data) => {
    // Custom order map for creature types
    const creatureTypeOrder = {
        "Avatar": 1,
        "Earth": 2,
        "Water": 3,
        "Air": 4,
        "Fire": 5
    };

    return Object.values(data.cards).sort((a, b) => {
        const aOrder = creatureTypeOrder[a.creatureTypes?.[0]] || Infinity;
        const bOrder = creatureTypeOrder[b.creatureTypes?.[0]] || Infinity;

        if (aOrder < bOrder) {
            return -1;
        }
        if (aOrder > bOrder) {
            return 1;
        }

        const aCost = a.cost;
        const bCost = b.cost;

        if (aCost < bCost) {
            return -1;
        }
        if (aCost > bCost) {
            return 1;
        }

        // If creatureTypes order is the same, compare the names
        return a.name.localeCompare(b.name);
    });
}

function descendingComparator(a, b, orderBy) {
    if (b[orderBy] < a[orderBy]) {
        return -1;
    }
    if (b[orderBy] > a[orderBy]) {
        return 1;
    }
    return 0;
}

function getComparator(order, orderBy) {
    return order === 'desc'
        ? (a, b) => descendingComparator(a, b, orderBy)
        : (a, b) => -descendingComparator(a, b, orderBy);
}

function stableSort(array, comparator) {
    const stabilizedThis = array.map((el, index) => [el, index]);
    stabilizedThis.sort((a, b) => {
        const order = comparator(a[0], b[0]);
        if (order !== 0) return order;
        return a[1] - b[1];
    });
    return stabilizedThis.map((el) => el[0]);
}


export default function SeventeenLandsPage() {
    const [cardPool, setCardPool] = useState([]);
    const [stats, setStats] = useState([]);
    const [order, setOrder] = useState('asc');
    const [orderBy, setOrderBy] = useState('name');

    const handleRequestSort = (event, property) => {
        const isAsc = orderBy === property && order === 'asc';
        setOrder(isAsc ? 'desc' : 'asc');
        setOrderBy(property);
    };

    useEffect(() => {
        fetch(`${URL}/api/seventeen_lands`)
        .then((response) => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json()
        })
        .then((data) => {
            setStats(data);
        })
    }, [])

    useEffect(() => {
        fetch(`${URL}/api/card_pool`)
        .then((response) => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return response.json();
        })
        .then((data) => {
          setCardPool(getOrganizedCardPool(data));
        })
        .catch((error) => {
          console.error('Error:', error);
        });
    }, []);

    const createSortHandler = (property) => (event) => {
        handleRequestSort(event, property);
    };

    const renderCellData = (data) => data != null ? formatPercentage(data) : '';

    return (
        <div>
            <Typography variant="h2">17Lands</Typography>
            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>
                                <TableSortLabel
                                    active={orderBy === 'name'}
                                    direction={orderBy === 'name' ? order : 'asc'}
                                    onClick={createSortHandler('name')}
                                >
                                    Name
                                </TableSortLabel>
                            </TableCell>
                            <TableCell align="right">
                                <TableSortLabel
                                    active={orderBy === 'win_rate'}
                                    direction={orderBy === 'win_rate' ? order : 'asc'}
                                    onClick={createSortHandler('win_rate')}
                                >
                                    Win Rate
                                </TableSortLabel>
                            </TableCell>
                            <TableCell align="right">
                                <TableSortLabel
                                    active={orderBy === 'pick_rate'}
                                    direction={orderBy === 'pick_rate' ? order : 'asc'}
                                    onClick={createSortHandler('pick_rate')}
                                >
                                    Pick Rate
                                </TableSortLabel>
                            </TableCell>
                            <TableCell align="right">Last Changed Time</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {stableSort(cardPool, getComparator(order, orderBy)).map((card) => (
                            <TableRow key={card.name}>
                                <TableCell component="th" scope="row">{card.name}</TableCell>
                                <TableCell align="right">{renderCellData(stats?.[card.name]?.win_rate)}</TableCell>
                                <TableCell align="right">{renderCellData(stats?.[card.name]?.pick_rate)}</TableCell>
                                <TableCell align="right">{new Date(stats?.[card.name]?.last_changed_time * 1000).toLocaleString()}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </div>
    );
}