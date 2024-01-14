import React, { useState, useCallback } from 'react';
import { useForm, Controller } from 'react-hook-form';
import {
  FormControl,
  FormLabel,
  Input,
  Button,
  Grid,
  Text,
  Container,
  Heading,
  Alert,
  Image,
  Flex,
  ChakraProvider,
  extendTheme,
} from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import TimeSlotSelector from './TimeSlotSelector';
import PhoneInput from 'react-phone-number-input';
import 'react-phone-number-input/style.css';
import muscle from './images/muscle.png'
import logo from './images/logo2.png';

const theme = extendTheme({
  styles: {
    global: {
      body: {
        bgGradient: "white",
        color: "black"
      },
    },
  },
  colors: {
    mistyRose: "rgb(255, 228, 225)",
    pink: "rgb(255, 194, 209)",
    cherryBlossomPink: "rgb(255, 179, 198)",
    rosePompadour: "rgb(251, 111, 146)"
    
  }
});

const SubscriptionForm = () => {
  const { handleSubmit, register, control } = useForm();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '', 
    phoneNumber: '',
    selectedSlots: [],
  });
  const [error, setError] = useState(null);
  const [selectedTimeSlots, setSelectedTimeSlots] = useState(Array(49).fill(false));

  const handleSlotSelection = useCallback((slots) => {
    setSelectedTimeSlots(slots);
  }, []);

  const onSubmit = async () => {
    const { username, phoneNumber } = formData;
    const schedule = selectedTimeSlots;

    console.log('Sending this data to the checkNumber endpoint:', {
      phoneNumber: phoneNumber,
    });

    console.log('Sending this data to the addClient endpoint:', {
      username: username,
      phoneNumber: phoneNumber,
      schedule: schedule
    });

    try {
      const response = await fetch('https://108f-2607-f470-6-3001-c0ed-23fc-5f64-23ce.ngrok-free.app/checkNumber', {
        method: 'POST',
        headers: {
          'accept': 'application/json',
        },
        body: new URLSearchParams({
          'phoneNumber': phoneNumber,
        }),
      });

      const responseData = await response.json();
      if (!response.ok) {
        setError('Error in checkNumber: ' + responseData.error);
        return;
      }

      const clientResponse = await fetch('https://108f-2607-f470-6-3001-c0ed-23fc-5f64-23ce.ngrok-free.app/addClient', {
        method: 'POST',
        headers: {
          'accept': 'application/json',
        },
        body: new URLSearchParams({
          'username': username,
          'phoneNumber': phoneNumber,
          'schedule': schedule
        }),
      });

      const clientData = await clientResponse.json();
      if (!clientResponse.ok) {
        setError('Error in adding client: ' + clientData.error);
        return;
      }

      navigate('/success');
    } catch (error) {
      setError('Error in API call: ' + error.message);
    }
  };

  return (
    <ChakraProvider theme={theme}>
      <Container centerContent minHeight='100vh' p={6} maxWidth="full">
        <Flex direction='row' alignItems='center' justifyContent='flex-start' mb={2}>
          <Image src={logo} alt="Logo" h="50px" w="50px" mr="2" />
          <Heading as="h1" size="2xl" fontWeight="bold" letterSpacing="tight">
            FitBuddy
          </Heading>
        </Flex>
        <Text color='black' fontSize='lg' fontWeight='bold' mt={2} mb={2}>
          Fill In Your Class Schedule To Be Loved By A Buddy
        </Text>

  
        <Flex width='100%' direction='row'>
          
          <Image 
            src={muscle}
            height="59vh" 
            width="auto" 
            objectFit="cover"
          />

          
          <Grid minH='80vh' p={6} gap={1} flex="1">
            <TimeSlotSelector
              onSelectSlot={handleSlotSelection}
              dayTextColor="#FF8FAB"
              selectedSlots={selectedTimeSlots}
            />
            {error && (
              <Alert status="error" mb={4}>
                {error}
              </Alert>
            )}
            <form onSubmit={handleSubmit(onSubmit)}>
              <FormControl id='username' isRequired mt={-4}>
                <FormLabel fontFamily="Roboto, sans-serif" color="rosePompadour">Username</FormLabel>
                <Controller
                  name='username'
                  control={control}
                  render={({ field }) => (
                    <Input
                      {...field}
                      placeholder='Username'
                      value={formData.username}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    />
                  )}
                />
              </FormControl>
              <FormControl id='phoneNumber' isRequired>
                <FormLabel fontFamily="Roboto, sans-serif" color="rosePompadour">Phone Number</FormLabel>
                <PhoneInput
                  placeholder='Enter phone number'
                  value={formData.phoneNumber}
                  onChange={(phone) => setFormData({ ...formData, phoneNumber: phone })}
                />
              </FormControl>
              <Button mt={4} colorScheme='pink' type='submit' bg='mistyRose' color='black'>
                Sign Up
              </Button>
            </form>
          </Grid>
        </Flex>
      </Container>
    </ChakraProvider>
  );
};

export default SubscriptionForm;