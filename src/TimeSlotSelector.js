import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Box, Text, Grid } from '@chakra-ui/react';

const TimeSlotSelector = ({ onSelectSlot, dayTextColor, selectedSlots, defaultSlotColor }) => {
  const [slots, setSlots] = useState(selectedSlots || Array(49).fill(false)); 
  const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const times = ["8:30-10:15", "10:15-12:00", "12:00-1:45", "1:45-3:30", "3:30-5:15", "5:15-7:00", "7:00-8:45"];
  
  useEffect(() => {
    if (selectedSlots) {
      setSlots(selectedSlots);
    }
  }, [selectedSlots]);

  const toggleSlot = (index) => {
    const newSlots = [...slots];
    newSlots[index] = !newSlots[index];
    setSlots(newSlots);
    onSelectSlot(newSlots);
  };

  return (
    <Grid templateColumns='repeat(7, 1fr)' gap={4}>
      {weekdays.map((day, dayIndex) => (
        <Box key={day} textAlign='center'>
          <Text fontSize='lg' color={dayTextColor}>{day}</Text>
          {times.map((time, slotIndex) => {
            const index = dayIndex * 7 + slotIndex;
            return (
              <Box 
                key={time}
                p={2}
                borderRadius='md'
                bg={slots[index] ? 'pink' : defaultSlotColor} 
                onClick={() => toggleSlot(index)}
                cursor='pointer'
              >
                {time}
              </Box>
            );
          })}
        </Box>
      ))}
    </Grid>
  );
};

TimeSlotSelector.propTypes = {
  onSelectSlot: PropTypes.func.isRequired,
  dayTextColor: PropTypes.string,
  selectedSlots: PropTypes.array, 
  defaultSlotColor: PropTypes.string, 
};

export default TimeSlotSelector;
