import React from 'react';
import { Box, Text, Heading } from '@chakra-ui/react';

const SubmissionPage = () => {
  return (
    <Box borderRadius='md' boxShadow='lg' p={6}>
      <Heading as='h4' size='lg' mb={3}>
        Thank You for Subscribing!
      </Heading>
      <Text fontSize='md'>
        Your form has been successfully submitted. We will contact you soon.
      </Text>
    </Box>
  );
};

export default SubmissionPage;
